# Основи Безпеки Вебзастосунків — Security Foundations

> **Для кого:** Студенти без попередніх знань з кібербезпеки.
>
> **Мета:** Побудувати фундамент — розуміти ЯК думає атакер, щоб будувати захист правильно.
>
> **Підхід:** Кожна тема починається з аналогії з реального світу, потім — теорія і код.

---

## 1. Три кити безпеки: CIA Triad

### Аналогія — банківський сейф

Уяви банківський сейф з документами:
- **Конфіденційність (C):** документи бачить лише власник. Сторонній — ні.
- **Цілісність (I):** ніхто не підмінив документи поки сейф був зачинений.
- **Доступність (A):** сейф відкривається коли власник приходить. Не "закрито на ремонт".

Порушити хоча б один з трьох — вже атака.

### CIA Triad у вебзастосунку

```mermaid
flowchart TB

    CIA["🛡️ CIA Triad"]

    CIA --> C["Конфіденційність"]
    CIA --> I["Цілісність"]
    CIA --> A["Доступність"]

    C --> C1["Авторизація"]
    C --> C2["Перевірка прав доступу"]

    I --> I1["CSRF захист"]
    I --> I2["Хешування паролів"]

    A --> A1["Rate limiting"]
    A --> A2["Захист від brute force"]
```

---

#  Django Security

```mermaid
flowchart LR

    User["👤 Користувач"]

    Auth["Authentication
Хто ти?"]

    Perm["Authorization
Що тобі дозволено?"]

    Resource["Дані системи"]

    User --> Auth

    Auth --> Perm

    Perm --> Resource
```

---
## ARCHITECT INSIGHT
```text

Confidentiality:
    хто бачить дані

Integrity:
    хто може змінювати дані

Availability:
    чи доступна система легітимним користувачам
```


### Приклади порушень і наслідки

| Порушення | Приклад атаки | Реальний наслідок |
|-----------|---------------|-------------------|
| **Конфіденційність** | Аліса читає нотатки Боба через IDOR | Витік особистих даних → штрафи GDPR |
| **Цілісність** | Атакер змінює ціну з $99 на $1 | Фінансові втрати компанії |
| **Доступність** | DDoS-атака 10 Gbps трафіку | Сайт недоступний → втрата клієнтів |

> **Важливо для початківця:** Більшість студентів думають про безпеку лише як
> про "щоб не вкрали пароль" (Confidentiality). Але підміна даних (Integrity)
> і недоступність (Availability) — теж атаки!

---

## 2. Межа довіри (Trust Boundary)

### Аналогія — митний контроль в аеропорту

Коли ти летиш з іншої країни, митниця перевіряє КОЖЕН твій чемодан. Вона не каже
"цей пасажир виглядає добре, пропустимо без огляду". Кожен проходить однакову перевірку.

**Trust Boundary в Django** — це те, де Django перевіряє кожен вхідний запит,
незалежно від того хто його надіслав.

### Шлях запиту: від браузера до БД

```mermaid
%%{init: {'flowchart': {'nodeSpacing': 60, 'rankSpacing': 80}}}%%
flowchart TD

    subgraph RED["🔴 Ненадійна зона"]
        Browser["🌐 Browser"]
        Attacker["👾 Attacker"]
    end

    subgraph YELLOW["🟡 Security Layer"]
        SpacerY[" "]
        Nginx["Nginx"]
        Middleware["Middleware"]
        Auth["Authentication"]
        Validation["Validation"]
        Permissions["Permissions"]
    end

    subgraph GREEN["🟢 Trusted Zone"]
        SpacerX[" "]
        View["Django View"]
        ORM["Django ORM"]
        DB["PostgreSQL"]
    end

    Browser --> SpacerY
    Attacker --> SpacerY
    SpacerY --> Nginx

    Nginx --> Middleware
    Middleware --> Auth
    Auth --> Validation
    Validation --> Permissions
    Permissions --> SpacerX
    SpacerX --> View
    View --> ORM
    ORM --> DB

    style RED fill:#4a2b2b,stroke:#ff5c5c,color:#ffffff
    style YELLOW fill:#4a432b,stroke:#f0c542,color:#ffffff
    style GREEN fill:#2b4a35,stroke:#4caf50,color:#ffffff

    style SpacerY fill:transparent,stroke:transparent,color:transparent
    style SpacerX fill:transparent,stroke:transparent,color:transparent
```

**Червона зона (ненадійна):** Будь-який запит з Інтернету. Будь-хто може підробити:
- HTTP заголовки (`X-Forwarded-For`, `Content-Type`)
- Тіло POST-запиту (`priority=999`, `is_admin=true`)
- Cookie (`sessionid=чужий_токен`)
- URL параметри (`?pk=42` — чужа нотатка)

**Зелена зона (довірена):** Всередині Django, після перевірок.

### Що Django перевіряє при перетині межі

```python
# Кожен вхідний запит проходить через цей ланцюг:

# 1. SecurityMiddleware — базові HTTP перевірки
# 2. SessionMiddleware — хто надсилає запит?
# 3. AuthenticationMiddleware — request.user встановлюється тут
# 4. CsrfViewMiddleware — чи є валідний CSRF токен?
# 5. Твій @login_required декоратор — залогінений?
# 6. forms.is_valid() — чи коректні дані форми?
# 7. get_object_or_404(..., user=request.user) — чи є право на цей об'єкт?

# Тільки після ВСІХ цих перевірок → довірена логіка
```

> **Правило:** Все що прийшло з Інтернету — **вважай підробленим** до перевірки.
> `request.POST`, `request.GET`, `request.FILES`, `request.COOKIES` — всі ненадійні.

---

## 3. Поверхня атаки (Attack Surface)

### Аналогія — кількість дверей у будинку

Замок з 10 дверима складніше охороняти ніж замок з 2 дверима. Кожна додаткова
двері — ще одна точка, яку треба захищати і яку може знайти атакер.

**Attack Surface** — загальна кількість "дверей" у твоєму застосунку.

### Всі точки входу у типовий Django-застосунок

```mermaid
%%{init: {'flowchart': {'nodeSpacing': 50, 'rankSpacing': 70}}}%%
flowchart LR

    A["👾 Атакер"]

    subgraph SURFACE["🔴 Поверхня атаки вебзастосунку"]
        U["URL endpoints<br/>/notes/, /admin/, /api/"]
        F["HTML форми<br/>&lt;input&gt;, &lt;textarea&gt;"]
        C["Cookies<br/>sessionid, csrftoken"]
        H["HTTP Headers<br/>Content-Type, User-Agent"]
        FI["File uploads<br/>.jpg, .pdf, .exe"]
        Q["Query params<br/>?search=..., ?pk=..."]
        D["Dependencies<br/>Django, Pillow, requests"]
    end

    A --> U
    A --> F
    A --> C
    A --> H
    A --> FI
    A --> Q
    A --> D

    classDef attacker fill:#ffcdd2,stroke:#c62828,color:#000000;
    classDef surface fill:#263238,stroke:#90a4ae,color:#ffffff;

    class A attacker;
    class U,F,C,H,FI,Q,D surface;

    style SURFACE fill:#3b2f2f,stroke:#ef5350,color:#ffffff
```

### Як зменшити Attack Surface в Django

```python
# settings.py — закрий все що не потрібно:

DEBUG = False                     # Прибирає debug-endpoints та детальні помилки
ALLOWED_HOSTS = ['mysite.com']    # Тільки твій домен, не '*' (відкриває всі)

# urls.py — можна прибрати /admin/ якщо не потрібен:
# path('admin/', admin.site.urls),  # ← закоментуй або зміни URL

# INSTALLED_APPS — прибери що не використовуєш:
INSTALLED_APPS = [
    # 'django.contrib.staticfiles',  # якщо статику сервить Nginx
    # 'debug_toolbar',               # НІКОЛИ в production!
]
```

**Чек-ліст зменшення Attack Surface:**
- ✓ `DEBUG = False` — прибирає `/500-debug-page/` та stack traces
- ✓ Специфічний `ALLOWED_HOSTS` — не `['*']`
- ✓ Прибрати `django-debug-toolbar` з `INSTALLED_APPS` в production
- ✓ Закрити тестові endpoints (`/dev/`, `/seed-data/`)
- ✓ Rate limiting на `/accounts/login/` і `/accounts/password_reset/`

---

## 4. Принцип Defense-in-Depth (Ешелонована Оборона)

### Аналогія — середньовічний замок

```
🏰 Середньовічний замок          ←→    Вебзастосунок

🌊 Рів з водою                   ←→    Firewall / DDoS захист (Cloudflare)
🧱 Зовнішні стіни               ←→    Nginx: rate limiting, HTTPS
⚔️  Охоронці при воротах         ←→    Django Middleware (CSRF, Sessions)
🚪 Внутрішні двері із замками    ←→    @login_required + object-level checks
🔐 Сховище зі скарбами           ←→    PostgreSQL + ORM (параметризовані запити)
📹 Відеоспостереження            ←→    Logging + SIEM моніторинг
```

**Головна ідея:** Якщо атакер перейде рів (обійде Firewall) — його зупинять стіни (Nginx).
Якщо обійде стіни — зупинять охоронці (Middleware). І так далі.

### Схема 6 рівнів захисту

```mermaid
%%{init: {'flowchart': {'nodeSpacing': 60, 'rankSpacing': 90}}}%%
flowchart TD

    Attack["🦹 Атакер"]

    subgraph DEFENSE["🛡️ Defense-in-Depth: 6 рівнів захисту"]
        L1["🌐 Рівень 1: Мережа<br/>Firewall<br/>DDoS protection<br/>HTTPS<br/>Cloudflare / AWS Shield"]

        L2["🧱 Рівень 2: Web Server<br/>Nginx<br/>Rate limiting<br/>HTTP Security Headers"]

        L3["⚙️ Рівень 3: Django Middleware<br/>SecurityMiddleware<br/>CSRF Middleware<br/>SessionMiddleware"]

        L4["🔐 Рівень 4: Application Layer<br/>@login_required<br/>Permissions<br/>get_object_or_404(..., user=request.user)"]

        L5["🗄️ Рівень 5: База даних<br/>Django ORM<br/>Параметризовані запити<br/>DB-user без DROP прав"]

        L6["📡 Рівень 6: Моніторинг<br/>Logging<br/>Sentry<br/>Grafana<br/>SIEM / Alerts"]
    end

    Data["✅ Дані захищені"]

    Attack --> L1
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> L5
    L5 --> L6
    L6 --> Data

    style Attack fill:#ffcdd2,stroke:#c62828,color:#000000
    style DEFENSE fill:#263238,stroke:#90a4ae,color:#ffffff

    style L1 fill:#fce4ec,stroke:#c62828,color:#000000
    style L2 fill:#fff3e0,stroke:#e65100,color:#000000
    style L3 fill:#fff9c4,stroke:#f9a825,color:#000000
    style L4 fill:#e8f5e9,stroke:#2e7d32,color:#000000
    style L5 fill:#e3f2fd,stroke:#1565c0,color:#000000
    style L6 fill:#f3e5f5,stroke:#6a1b9a,color:#000000
    style Data fill:#c8e6c9,stroke:#2e7d32,color:#000000
    
```

### Що відбувається якщо один рівень пробито

```mermaid
%%{init: {'flowchart': {'nodeSpacing': 60, 'rankSpacing': 80}}}%%
flowchart TD

    Attack["🦹 Атакер"]
    Bypass["⚠️ Рівень 2 пробито<br/>Nginx rate limiting обійдено<br/>через VPN-ротацію"]

    subgraph BAD["❌ Без Defense-in-Depth"]
        Bad1["Nginx пропустив"]
        Bad2["Brute-force триває"]
        Bad3["💀 GAME OVER<br/>пароль підібрано"]
    end

    subgraph GOOD["✅ З Defense-in-Depth"]
        Good1["Nginx пропустив"]
        Good2["Django Middleware перевіряє запит"]
        Good3["CSRF / Session / Auth перевірки"]
        Good4["🛡️ Запит заблоковано"]
    end

    Attack --> Bypass

    Bypass --> Bad1
    Bad1 --> Bad2
    Bad2 --> Bad3

    Bypass --> Good1
    Good1 --> Good2
    Good2 --> Good3
    Good3 --> Good4

    style Attack fill:#ffcdd2,stroke:#c62828,color:#000000
    style Bypass fill:#ffecb3,stroke:#ff6f00,color:#000000

    style BAD fill:#3b1f1f,stroke:#c62828,color:#ffffff
    style GOOD fill:#1b3b2a,stroke:#2e7d32,color:#ffffff

    style Bad1 fill:#ffcdd2,stroke:#c62828,color:#000000
    style Bad2 fill:#ef9a9a,stroke:#c62828,color:#000000
    style Bad3 fill:#b71c1c,stroke:#ffffff,color:#ffffff

    style Good1 fill:#fff9c4,stroke:#f9a825,color:#000000
    style Good2 fill:#e8f5e9,stroke:#2e7d32,color:#000000
    style Good3 fill:#c8e6c9,stroke:#2e7d32,color:#000000
    style Good4 fill:#a5d6a7,stroke:#1b5e20,color:#000000
```

```
Сценарій: Атакер обійшов Nginx rate limiting через VPN-ротацію.

Без Defense-in-Depth:
  Nginx → пропущено → GAME OVER (брут-форс паролів успішний)

З Defense-in-Depth:
  Nginx → пропущено
  → Django Middleware: CSRF перевірка не пройшла → заблоковано ✓

Або інший сценарій: атакер вкрав sessionid cookie.

Без Defense-in-Depth:
  Він входить і бачить ВСІ дані → GAME OVER

З Defense-in-Depth:
  Він входить → бачить ТІЛЬКИ дані власника сесії
  → get_object_or_404(Note, pk=pk, user=request.user) → чужі нотатки недоступні ✓
```
___

## 5. Аутентифікація vs Авторизація

### Аналогія — паспорт і квиток на концерт

- **Паспорт** = Аутентифікація (AuthN): "Хто ти?" — підтверджує особу
- **Квиток** = Авторизація (AuthZ): "Куди тобі можна?" — визначає права

У аеропорту: охорона перевіряє паспорт (AuthN), потім посадковий талон (AuthZ).
Паспорт без квитка — не пустять. Квиток без паспорта — теж.

### Повний flow аутентифікації в Django

```mermaid
sequenceDiagram
    participant Б as Браузер
    participant V as Django View
    participant DB as База даних

    Б->>V: POST /accounts/login/ {username, password}
    V->>DB: authenticate(username, password)
    Note over DB: Знаходить юзера<br/>Порівнює PBKDF2 хеші
    DB-->>V: User object (або None)
    
    alt Хеш збігається
        V->>DB: login() — створює session запис
        DB-->>V: session_key = "xK9mPq..."
        V-->>Б: 302 Redirect + Set-Cookie: sessionid=xK9mPq...
    else Не збігається
        V-->>Б: 200 + форма з помилкою "Невірний логін"
    end
```

### Дерево рішень авторизації

```mermaid
%%{init: {'flowchart': {'nodeSpacing': 70, 'rankSpacing': 90}}}%%
flowchart TD

    R["🌐 Запит<br/>/notes/42/edit/"]

    Q1{"request.user<br/>аутентифікований?"}

    R1["🔁 302 Redirect<br/>/accounts/login/"]

    Q2{"note.user<br/>== request.user?"}

    A1["✅ Доступ надано<br/>показати форму редагування"]

    Q3{"user є членом<br/>note.group?"}

    A2["👁️ Груповий доступ<br/>дозволити перегляд<br/>редагування заборонено"]

    A3["⛔ 403 Forbidden<br/>PermissionDenied"]

    R --> Q1

    Q1 -->|НІ| R1
    Q1 -->|ТАК| Q2

    Q2 -->|ТАК| A1
    Q2 -->|НІ| Q3

    Q3 -->|ТАК| A2
    Q3 -->|НІ| A3

    style R fill:#e3f2fd,stroke:#1565c0,color:#000000
    style Q1 fill:#fff9c4,stroke:#f9a825,color:#000000
    style Q2 fill:#fff9c4,stroke:#f9a825,color:#000000
    style Q3 fill:#fff9c4,stroke:#f9a825,color:#000000

    style R1 fill:#fff3e0,stroke:#e65100,color:#000000
    style A1 fill:#c8e6c9,stroke:#2e7d32,color:#000000
    style A2 fill:#e3f2fd,stroke:#1565c0,color:#000000
    style A3 fill:#ffcdd2,stroke:#c62828,color:#000000
```

### Django реалізація

```python
# Аутентифікація (хто ти?):
from django.contrib.auth import authenticate, login

user = authenticate(request, username='alice', password='secret')
if user is not None:
    login(request, user)   # ← створює сесію в БД
    # тепер request.user = alice у всіх наступних запитах

# Авторизація (що тобі можна?):
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

@login_required                                        # ← AuthN: залогінений?
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if note.user != request.user:                      # ← AuthZ: власник?
        raise PermissionDenied                         # 403 Forbidden
    # або коротше:
    note = get_object_or_404(Note, pk=pk, user=request.user)  # AuthN + AuthZ разом
```

> **Часта помилка:** `@login_required` — це ТІЛЬКИ AuthN. Він не перевіряє
> чи цей конкретний об'єкт belongs to юзеру. Потрібні обидві перевірки!

---

## 6. Хешування паролів — чому MD5 небезпечний

### Аналогія — м'ясорубка (одностороння функція)

М'ясо → м'ясорубка → фарш. Повернути фарш назад у цілий шматок м'яса — неможливо.
Хеш-функція працює так само: пароль → хеш-функція → хеш. Відновити пароль з хешу —
математично нездійсненно (для гарного алгоритму).

### Чому MD5 — неправильний вибір

MD5 розроблявся у 1991 році як контрольна сума (не для паролів!). Він надзвичайно швидкий.

```
Порівняння швидкості (на сучасній GPU RTX 4090):

MD5:      60,000,000,000 хешів/секунду (60 мільярдів!)
bcrypt:        20,000 хешів/секунду
PBKDF2:        10,000 хешів/секунду

Brute-force паролю "Password1" (8 символів, A-z + 0-9):
  MD5:    < 1 секунди   ← НЕБЕЗПЕЧНО
  bcrypt: ~3 доби       ← прийнятно  
  PBKDF2: ~7 діб        ← ДОБРЕ
```

**Ключовий принцип:** Для паролів "повільно = безпечно". Алгоритм навмисно повільний,
щоб brute-force атака коштувала роки часу навіть на суперкомп'ютері.

### Таблиця порівняння алгоритмів

| Алгоритм | Швидкість | Salt | Безпечний? | Де використовують |
|----------|-----------|------|------------|-------------------|
| MD5 | ~60 Ghash/s | ✗ | ❌ НІ | Контрольні суми файлів |
| SHA-256 | ~20 Ghash/s | ✗ | ❌ НІ для паролів | Підписи (не паролі!) |
| bcrypt | ~20k/s | ✓ | ✅ ТАК | PHP, Ruby проєкти |
| PBKDF2 | ~10k/s | ✓ | ✅ ТАК | **Django за замовчуванням** |
| Argon2 | ~1k/s | ✓ | ✅ ТАК | Найсучасніший (Django 3+) |

### Що зберігається в БД Django

```
Поле User.password у базі даних:

pbkdf2_sha256$720000$randomsalt$VQaFwT...longhash...==
│             │       │           │
│             │       │           └─ власне хеш (base64)
│             │       └─ сіль (random, 22 символи)
│             └─ кількість ітерацій (720000 у Django 5.x)
└─ назва алгоритму
```

```python
# Django автоматично хешує при set_password():
user = User.objects.create_user(username='alice', password='secret123')
print(user.password)
# → 'pbkdf2_sha256$720000$xK9mPq3rT8aL2v...=$VQaFwT+abc...=='

# Django автоматично перевіряє при authenticate():
user = authenticate(request, username='alice', password='secret123')
# → Django: PBKDF2('secret123', salt='xK9mPq3rT8aL2v...', iterations=720000)
# → Порівнює з хешем у БД
# → Повертає User якщо збігається, None якщо ні
```

### Чому salt важливий

```
БЕЗ SALT — Rainbow Table атака:

Атакер завчасно обчислює таблицю:
  "password"  → "5f4dcc3b5aa765d61d8327deb882cf99"
  "123456"    → "e10adc3949ba59abbe56e057f20f883e"
  "qwerty"    → "d8578edf8458ce06fbc5bb76a58c5ca4"
  ...мільярди записів...

Отримав хеш з БД: "5f4dcc3b5aa765d61d8327deb882cf99"
→ Знаходить у таблиці за 0.001 секунди → пароль "password" ✓

З SALT — Rainbow Table марна:

  "password" + "xK9mPq" (у Аліси) → "АБСОЛЮТНО УНІКАЛЬНИЙ хеш"
  "password" + "mR7pLw" (у Боба)  → "ІНШИЙ УНІКАЛЬНИЙ хеш"

Навіть якщо Аліса і Боб мають ОДНАКОВИЙ пароль — хеші різні.
Попередньо обчислена таблиця марна: доведеться brute-force кожен акаунт окремо.
```

---

## 7. CSRF — Cross-Site Request Forgery

### Аналогія — підроблений лист від твого імені

Уяви: банк приймає перекази за листами з твоїм підписом. Атакер підробляє твій підпис
і надсилає лист "перекажіть $1000 на мій рахунок". Банк не знає що лист підроблений.

CSRF — це те саме, але в браузері: атакер змушує **твій браузер** надіслати запит
від твого імені (з твоїми cookies), без твого відома.

### CSRF атака: покроково

```mermaid
sequenceDiagram
    participant Б as Браузер Аліси
    participant E as evil.com
    participant D as bank.com

    Note over Б,D: Аліса залогінена на bank.com (sessionid cookie є)
    
    Б->>E: Аліса відкриває evil.com
    E-->>Б: HTML з прихованою формою:
    Note over E,Б: <form action="bank.com/transfer"><br/>  <input value="hacker_account"><br/>  <input value="1000"><br/></form><br/><script>form.submit()</script>
    Б->>D: POST /transfer amount=1000 to=hacker
    Note over Б,D: Cookie sessionid автоматично додається браузером!
    D-->>Б: Переказ виконано (bank.com думав що це Аліса)
```

### CSRF захист: з токеном

```mermaid
sequenceDiagram
    participant Б as Браузер Аліси
    participant E as evil.com
    participant D as bank.com (з CSRF захистом)

    Б->>D: GET /transfer (перша відкриття сторінки)
    D-->>Б: HTML з CSRF токеном: csrfmiddlewaretoken=abc123xyz
    Note over Б: Токен прив'язаний до сесії Аліси
    
    Б->>E: Аліса відкриває evil.com
    E-->>Б: Форма без CSRF токена (evil.com не знає abc123xyz!)
    Б->>D: POST без csrfmiddlewaretoken
    D-->>Б: 403 Forbidden — CSRF перевірка не пройшла ✓
```

### Django реалізація

```html
<!-- Кожна POST-форма ОБОВ'ЯЗКОВО має {% csrf_token %}: -->
<form method="POST" action="{% url 'note_create' %}">
    {% csrf_token %}
    <!-- Django генерує: -->
    <!-- <input type="hidden" name="csrfmiddlewaretoken" value="abc123...xyz"> -->
    
    {{ form.as_p }}
    <button type="submit">Зберегти</button>
</form>
```

```python
# settings.py — налаштування CSRF та Cookies:
SESSION_COOKIE_SAMESITE = "Lax"
# ↑ "Lax": cookie надсилається при навігації всередині сайту,
#   але НЕ надсилається при крос-сайтових POST запитах.
#   Тобто evil.com → bank.com не отримає sessionid автоматично.

# "Strict": cookie взагалі не надсилається при будь-якому крос-сайтовому запиті.
#   Жорсткіше, але ламає деякі OAuth flows.

# "None": завжди надсилається (НЕБЕЗПЕЧНО, потрібен Secure flag).
```

### SameSite: порівняння режимів

| SameSite | Навігація (a → b) | Cross-site POST | OAuth редиректи | Рекомендація |
|----------|-------------------|-----------------|-----------------|--------------|
| `Strict` | ✗ не надсилається | ✗ | ✗ | Максимальна безпека |
| `Lax` | ✓ надсилається | ✗ | ✓ | **Рекомендовано для Django** |
| `None` | ✓ | ✓ | ✓ | Тільки з `Secure` прапором |

---

## 8. Безпека файлових завантажень

### Аналогія — митниця і рентген

Прикордонник може перевірити паспорт (розширення файлу `.jpg`) — але назву можна підробити.
Рентген перевіряє ВМІСТ валізи (magic bytes файлу) — це підробити набагато складніше.

**Правило:** Ніколи не довіряй розширенню файлу. Завжди перевіряй справжній тип через вміст.

### Небезпечні розширення та що з ними роблять атакери

| Розширення | Небезпека | Атака |
|------------|-----------|-------|
| `.php`, `.py`, `.sh` | Виконання коду на сервері (RCE) | Завантажити webshell, перейменувавши в `.jpg` |
| `.html`, `.svg` | XSS | `<script>` у SVG або HTML файлі |
| `.exe`, `.bat` | Зараження клієнта | Соціальна інженерія через download |
| `.zip` (Zip Bomb) | DoS | 1 КБ архів → 1 ТБ після розпакування |

### Покроковий захист

```python
# 1. Перевірка розширення (перший бар'єр):
from django.core.validators import FileExtensionValidator

class AvatarUploadForm(forms.Form):
    avatar = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    # ↑ Відхиляє .php, .exe — але атакер може перейменувати. Потрібен крок 2!

# 2. Перевірка magic bytes (справжній тип):
import magic    # pip install python-magic-bin (Windows) або python-magic (Linux)

def validate_image_content(file):
    file_content = file.read(2048)
    file.seek(0)  # повернути курсор — Django читатиме файл далі
    
    mime_type = magic.from_buffer(file_content, mime=True)
    allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
    
    if mime_type not in allowed_types:
        raise forms.ValidationError(
            f"Недійсний тип файлу: {mime_type}. Дозволено: JPEG, PNG, WebP."
        )

# 3. Безпечне ім'я файлу (UUID замість оригінального імені):
import uuid
from pathlib import Path

def upload_to(instance, filename):
    ext = Path(filename).suffix.lower()   # .jpg
    new_name = f"{uuid.uuid4()}{ext}"     # 550e8400-e29b-41d4-a716-446655440000.jpg
    return f"avatars/{new_name}"
    # Атакер не може передбачити URL завантаженого файлу
```

```python
# 4. Зберігання ПОЗА web root:
MEDIA_ROOT = '/var/uploads/private/'   # НЕ /var/www/uploads/ !

# Django view для роздачі файлів:
@login_required
def serve_avatar(request, filename):
    note = get_object_or_404(Note, avatar_filename=filename, user=request.user)
    file_path = Path(settings.MEDIA_ROOT) / filename
    return FileResponse(open(file_path, 'rb'), content_type='image/jpeg')
# ↑ Файл доступний тільки через Django view, а не напряму через Nginx
```

---

## 9. Принцип найменших привілеїв (Least Privilege)

### Аналогія — система ключів в офісі

Охоронець має ключ від головного входу (може відчинити офіс). Але у нього НЕМАЄ ключа
від сейфу директора, від серверної кімнати, від бухгалтерії. Він має рівно стільки доступу,
скільки потрібно для його роботи — і не більше.

**Least Privilege** = кожен компонент системи має мінімально необхідні права.

### Django компоненти та їх мінімальні права

| Компонент | Мінімальні права | ЩО НЕ треба давати |
|-----------|------------------|--------------------|
| Django DB user | SELECT, INSERT, UPDATE, DELETE | CREATE DB, DROP TABLE, GRANT |
| Celery worker | підключення до Redis/RabbitMQ | адмін права БД |
| Email service | SMTP відправка | IMAP/POP3 читання |
| S3 bucket policy | `s3:PutObject`, `s3:GetObject` | `s3:DeleteBucket`, `s3:*` |
| Nginx процес | читання `/var/www/` | запис у `/etc/` |

### Налаштування окремого DB-юзера (PostgreSQL)

```sql
-- Підключитись як postgres superuser:
-- psql -U postgres

-- 1. Створити окремого юзера для Django:
CREATE USER django_user WITH PASSWORD 'strongpassword';

-- 2. Дати права ТІЛЬКИ на конкретну БД:
GRANT CONNECT ON DATABASE mydb TO django_user;

-- 3. Дати права на схему:
GRANT USAGE ON SCHEMA public TO django_user;

-- 4. Дати права на операції (без DROP, CREATE, GRANT!):
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO django_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO django_user;

-- Якщо атакер зламає Django → він може лише читати/писати дані
-- але НЕ може: DROP TABLE users; або CREATE USER hacker SUPERUSER;
```

```python
# settings.py:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        'USER': 'django_user',     # ← окремий юзер, не 'postgres'!
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## 10. Секрети та Environment Variables

### Аналогія — пароль на стікері vs пароль у голові

Пароль написаний на стікері, приклеєному до монітора — бачить кожен хто проходить мимо.
Те саме відбувається з секретами у коді: git commit → GitHub → PUBLIC репозиторій → всі бачать.

### Проблема: git зберігає ВСЮ ІСТОРІЮ

```bash
# Навіть якщо ти видалив SECRET_KEY з settings.py і зробив commit —
# він ЗАЛИШАЄТЬСЯ в git history і його можна знайти:

git log --all --full-history -p -- "*.py" | grep "SECRET_KEY"
# → Покаже всі коміти де SECRET_KEY змінювався

# Атакери сканують GitHub в пошуку таких витоків:
# GitGuardian, TruffleHog — автоматичні сканери secrets у git
```

### Правильне рішення: .env файл + python-decouple

```bash
# Крок 1: .env файл (НІКОЛИ не комітити в git!)
# Файл: crispy_notes_project/.env

SECRET_KEY=django-very-random-key-50-chars-here
DATABASE_URL=postgresql://django_user:strongpassword@localhost:5432/mydb
EMAIL_HOST_PASSWORD=smtp_password_here
DEBUG=False
```

```python
# Крок 2: pip install python-decouple
# settings.py:

from decouple import config, Csv

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='mydb'),
        'USER': config('DB_USER', default='django_user'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
    }
}
```

```bash
# Крок 3: .gitignore (ОБОВ'ЯЗКОВО):
echo ".env" >> .gitignore
echo "*.env" >> .gitignore

# Перевірити що .env не потрапляє в git:
git status   # .env не має з'являтися у списку
git check-ignore -v .env   # → .gitignore:1:.env  .env  (ігнорується)
```

```bash
# Крок 4: .env.example — шаблон для нових розробників (БЕЗ реальних значень):
# .env.example (цей файл МОЖНА комітити):

SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
EMAIL_HOST_PASSWORD=your-smtp-password
DEBUG=True
```

---

## 11. Безпечні HTTP Заголовки

### Як це працює: браузер читає заголовки і застосовує правила

```mermaid
sequenceDiagram
    participant Б as Браузер
    participant D as Django (SecurityMiddleware)

    Б->>D: GET /notes/
    D-->>Б: HTTP/1.1 200 OK
    Note over D,Б: X-Frame-Options: DENY<br/>X-Content-Type-Options: nosniff<br/>Strict-Transport-Security: max-age=31536000<br/>Referrer-Policy: same-origin
    
    Note over Б: Браузер застосовує правила:<br/>— Не завантажуватиме цю сторінку у iframe<br/>— Не вгадуватиме MIME-тип файлів<br/>— Завжди використовуватиме HTTPS<br/>— Не надсилатиме Referer на зовнішні сайти
```

### Детальний розбір кожного заголовку

**`X-Frame-Options: DENY`** — захист від Clickjacking

```
Атака Clickjacking:
1. Атакер розміщує твій сайт у прихованому <iframe> на evil.com
2. Поверх iframe — підроблені кнопки ("Натисни тут щоб отримати приз!")
3. Юзер "натискає на приз" — насправді натискає на кнопку "Видалити акаунт" твого сайту

Захист X-Frame-Options: DENY → браузер відмовляється завантажувати сторінку в <iframe>
```

```python
# settings.py:
X_FRAME_OPTIONS = 'DENY'          # Забороняє будь-який iframe
# або:
X_FRAME_OPTIONS = 'SAMEORIGIN'    # Дозволяє iframe тільки з того ж домену
```

**`X-Content-Type-Options: nosniff`** — захист від MIME sniffing

```
Атака:
1. Атакер завантажує файл "photo.jpg" який насправді є JavaScript
2. Браузер "нюхає" вміст і каже: "Схоже на JS, запущу як скрипт!"
3. XSS атака через завантажений файл

Захист nosniff → браузер завжди використовує Content-Type з заголовку, ніколи не "вгадує"
```

**`Strict-Transport-Security: max-age=31536000`** — примусовий HTTPS

```
Атака SSL Stripping:
1. Юзер вводить "mybank.com" (без https://)
2. Атакер "в середині" перехоплює і встановлює HTTP з'єднання з юзером
3. Паролі передаються відкритим текстом

Захист HSTS → після першого HTTPS відвідування браузер ЗАВЖДИ використовує HTTPS
              і не приймає HTTP відповідь навіть якщо сервер її надсилає
```

**`Content-Security-Policy`** — захист від XSS

```
Без CSP:
  Атакер вставляє <script src="evil.com/steal.js"> → браузер завантажує і виконує

З CSP: default-src 'self':
  Браузер завантажує скрипти ТІЛЬКИ з поточного домену → evil.com/steal.js заблоковано
```

```python
# settings.py — всі заголовки безпеки:
SECURE_CONTENT_TYPE_NOSNIFF = True          # nosniff
X_FRAME_OPTIONS = 'DENY'                    # clickjacking
SECURE_REFERRER_POLICY = 'same-origin'      # не витікає URL у Referer заголовку

# Production HTTPS (розкоментуй коли є SSL):
# SECURE_SSL_REDIRECT = True                # HTTP → HTTPS редирект
# SECURE_HSTS_SECONDS = 31536000            # HSTS на 1 рік
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True     # поширюється на піддомени
# SESSION_COOKIE_SECURE = True              # sessionid тільки по HTTPS
# CSRF_COOKIE_SECURE = True                 # csrftoken тільки по HTTPS
```

### Перевірка через Django check

```bash
python manage.py check --deploy

# Приклад output:
# WARNINGS:
# ?: (security.W004) You have not set SESSION_COOKIE_SECURE to True.
# ?: (security.W008) Your SECRET_KEY has less than 50 characters.
# ?: (security.W012) SESSION_COOKIE_HTTPONLY is not set to True.
# ?: (security.W018) You should not have DEBUG set to True in deployment.
#
# Кожне попередження — конкретна вразливість!
```

---

## 12. Чек-ліст перед деплоєм

### Категорія 1: Основні налаштування

```python
# settings.py:
DEBUG = False                               # ❌ Ніколи True в production

SECRET_KEY = os.environ['SECRET_KEY']       # ❌ Не hardcoded рядок
# Як згенерувати новий SECRET_KEY:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

ALLOWED_HOSTS = ['mysite.com', 'www.mysite.com']  # ❌ Не ['*']
```

### Категорія 2: HTTPS

```python
# Розкоментуй після встановлення SSL-сертифіката:
SECURE_SSL_REDIRECT = True           # HTTP → HTTPS
SESSION_COOKIE_SECURE = True         # Cookie тільки по HTTPS
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000       # Браузер пам'ятає HTTPS 1 рік
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

### Категорія 3: Database

```bash
# Окремий DB-юзер з мінімальними правами (не postgres!):
# CREATE USER django_user WITH PASSWORD 'strongpassword';
# GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO django_user;
```

### Категорія 4: Секрети

```bash
# .env файл — НЕ в git:
git status             # .env не з'являється у списку
cat .gitignore | grep env    # → .env  (присутній!)

# Перевірити що secrets не в git history:
git log --all --full-history -p -- settings.py | grep "SECRET_KEY ="
```

### Категорія 5: Залежності

```bash
# Перевірка вразливостей:
pip-audit                      # pip install pip-audit

# Перевірка застарілих пакетів:
pip list --outdated

# Фіксовані версії у requirements.txt (не >=, а ==):
# Django==5.2.14
# django-crispy-forms==2.3.3
```

### Категорія 6: Django Security Check

```bash
python manage.py check --deploy
# Має показати: System check identified no issues (0 silenced).
# Якщо є WARNINGS — це реальні вразливості!
```

### Категорія 7: Логування

```python
# settings.py — базове логування для production:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/security.log',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
```

---

> **Підсумок:** Безпека — це не один `@login_required`. Це **шари**: налаштування,
> хешування, CSRF, заголовки, мінімальні права, моніторинг. Кожен шар важливий.
> Пропустиш один — атакер знайде.
