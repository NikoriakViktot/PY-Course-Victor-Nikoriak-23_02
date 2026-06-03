# Zero Trust Architecture — Архітектура Нульової Довіри

> **"Never trust, always verify"** — жодного користувача, пристрою чи мережі
> не вважати безпечним лише тому, що він "всередині" системи.
>
> **Аналогія:** Навіть якщо співробітник щодня проходить через турнікет в офіс,
> кожного разу коли він відкриває двері до серверної кімнати —
> система знову перевіряє його картку. Це Zero Trust.

---

## Що таке Zero Trust?

**Архітектура нульової довіри (Zero Trust Architecture)** — це філософія та шаблон проєктування безпеки, яка відмовляється від поняття "неявної довіри" на основі:
- Перебування користувача чи пристрою у внутрішній мережі
- Попередньої успішної автентифікації

Принцип: **"ніколи не довіряй, завжди перевіряй"** — явне підтвердження особи та дозволів для **кожного запиту** до системи.

> **Важливо:** Архітектура Zero Trust — це не продукт, який можна "купити і встановити".
> Це підхід до проєктування системи, де кожен компонент за замовчуванням не довіряє іншим.

### 6 ключових принципів Zero Trust

**1. Безперервна перевірка (Continuous Verification)**

Проста наявність токена чи факту входу в систему не означає, що користувачу можна довіряти постійно. Кожна привілейована дія має проходити перевірку. Сліпа довіра до токена — серйозна вразливість.

**2. Принцип найменших привілеїв (Least Privilege)**

Кожен користувач, пристрій або скрипт отримує доступ лише до того, що йому абсолютно необхідно. Якщо менеджеру потрібен доступ до меню кафетерію — він не повинен бачити корпоративну базу даних клієнтів.

**3. Суворе управління ідентифікацією (IAM)**

Система має чітко знати ВСІХ: людей, пристрої, програми. Тактики:
- **MFA (Багатофакторна автентифікація):** пароль + смартфон + біометрія
- **SSO (Single Sign-On):** один надійний провайдер автентифікації

**4. Мікросегментація (Micro-segmentation)**

Замість загального доступу до всього середовища — суворі правила для кожного відділу, юзера, пристрою. Якщо зловмисник отримає доступ до одного ресурсу — він не може автоматично дістатися до інших.

**5. Постійний моніторинг (Continuous Monitoring)**

Реєструй і перевіряй весь мережевий трафік. Стеж за всіма сутностями — чи не виходять вони за межі своїх повноважень.

**6. Захист на рівні фреймворку**

Правильне використання вбудованих механізмів безпеки (CSRF-захист в Django, параметризовані запити ORM) — частина Zero Trust підходу.

---

## 1. Безперервна авторизація (Continuous Verification)

Zero Trust вимагає перевірки **кожного виклику привілейованої функції**, а не лише одноразового входу.

> Наявність дійсного токена не означає безумовної довіри — статус користувача міг змінитися.

**Django реалізація:**
```python
# НЕ достатньо — перевірка тільки при вході:
@login_required
def edit_note(request, pk):
    note = get_object_or_404(Note, pk=pk)  # IDOR вразливість!

# Zero Trust — перевірка на кожному запиті:
@login_required
@permission_required('hello_app.change_note')
def edit_note(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)  # ← явна перевірка
```

---

## 2. Контроль доступу на рівні об'єктів (Object-Level Permissions)

Глобальних дозволів недостатньо для Zero Trust. Необхідна перевірка власності конкретного об'єкта.

**Проблема IDOR:**
```python
# Аліса знає URL: /notes/42/edit/
# Нотатка 42 належить Бобу. Без перевірки:
note = get_object_or_404(Note, pk=42)   # Аліса отримує доступ!

# Zero Trust — перевірка власника:
note = get_object_or_404(Note, pk=42, user=request.user)  # 404 для Аліси
```

**Для групового доступу:**
```python
from django.core.exceptions import PermissionDenied
from django.db.models import Q

def check_note_access(note, user):
    user_groups = user.groups.all()
    has_access = (
        note.user == user or                          # власник
        (note.group and note.group in user_groups)    # член групи
    )
    if not has_access:
        raise PermissionDenied
```

**Рекомендація:** Використовуй UUID замість auto-incrementing integer PK для важливих об'єктів — неможливо вгадати наступний ID.

---

## 3. Сувора валідація даних (Zero Trust Input)

Жодному вводу з боку клієнта не можна довіряти неявно.

```python
# НЕ достатньо — тільки фронтенд-валідація:
# <input type="number" min="1" max="100">  ← атакер обходить

# Zero Trust — серверна валідація в моделі:
class Note(models.Model):
    priority = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    
    def clean(self):
        if self.priority not in [1, 2, 3, 4]:
            raise ValidationError("Недійсний пріоритет")

# або в формі:
class NoteForm(forms.ModelForm):
    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 3:
            raise forms.ValidationError("Заголовок занадто короткий.")
        return title
```

---

## 4. Багатофакторна автентифікація (MFA)

Zero Trust значною мірою спирається на MFA — звичайні паролі легко компрометуються.

```python
# Встановлення:
pip install django-two-factor-auth

# settings.py:
INSTALLED_APPS += ['two_factor']
LOGIN_URL = 'two_factor:login'
TWO_FACTOR_PATCH_ADMIN = True

# urls.py:
from two_factor.urls import urlpatterns as tf_urls
urlpatterns = [path('', include(tf_urls)), ...]
```

**Фактори:**
- **Знання** — пароль
- **Посідання** — OTP-код (Google Authenticator, SMS)
- **Притаманне** — біометрія (FaceID, відбиток)

---

## 5. Мікросегментація та Моніторинг

Zero Trust використовує постійний моніторинг для виявлення аномалій.

```python
# settings.py — розширений security logging:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'security_file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
        },
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# views.py — логування привілейованих дій:
import logging
security_log = logging.getLogger('django.security')

@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST':
        security_log.warning(
            f"User {request.user.pk} deleted note {pk}",
            extra={'request': request}
        )
        note.delete()
```

---

## 6. Continuous Verification — Безперервна перевірка (Деталі)

**Continuous Verification** — ключовий компонент Zero Trust. Простого факту попередньої автентифікації недостатньо. Система повинна **перевіряти кожен виклик привілейованої функції**.

### 6.1 Централізована перевірка доступу

Щоб уникнути ручного додавання перевірок у кожній функції — централізуй логіку:

```python
# DRF: кастомний клас дозволів
from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

# Глобально у settings.py:
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['hello_app.permissions.IsOwner'],
}

# Для звичайних views — використовуй міксини:
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

class NoteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'hello_app.change_note'
    # Авторизація виконується ДО бізнес-логіки
```

### 6.2 Middleware як глобальний щит

Кастомний Middleware, що блокує всі незахищені endpoints:

```python
# hello_app/middleware.py
class RequireAuthMiddleware:
    PUBLIC_URLS = ['/accounts/login/', '/accounts/register/', '/']
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path not in self.PUBLIC_URLS:
            if not request.user.is_authenticated:
                from django.shortcuts import redirect
                return redirect('login')
        return self.get_response(request)
```

### 6.3 Валідація стану JWT-токена (для API)

Проблема JWT: токен дійсний до закінчення терміну, навіть якщо юзера заблоковано.

```python
# Рішення: blacklist + Redis перевірка при кожному запиті
# pip install djangorestframework-simplejwt[crypto]

# settings.py:
INSTALLED_APPS += ['rest_framework_simplejwt.token_blacklist']

# При logout — додаємо токен у blacklist:
from rest_framework_simplejwt.tokens import RefreshToken

def logout_api(request):
    refresh_token = request.data.get('refresh')
    token = RefreshToken(refresh_token)
    token.blacklist()   # Redis: занести в список відкликаних
```

### 6.4 Перевірка на рівні об'єктів (IDOR Prevention)

```python
# ПОГАНО — перевіряємо лише "чи є роль":
@login_required
def edit_note(request, pk):
    note = get_object_or_404(Note, pk=pk)   # IDOR! Alice редагує нотатку Bob-а

# ДОБРЕ — перевіряємо право на конкретний об'єкт:
@login_required
def edit_note(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if note.user != request.user:
        raise PermissionDenied   # Continuous verification!
    # ...
```

### 6.5 Захист від Mass Assignment

```python
# Атака: POST {'is_admin': True} → зміна ролі

# НЕ безпечно:
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'  # ← атакер може надіслати is_superuser=True!

# БЕЗПЕЧНО — явна whitelist полів:
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['display_name', 'bio', 'timezone']  # ← тільки ті що дозволено
```

---

## Zero Trust у нашому проєкті

| Принцип ZT | Реалізація в crispy_notes_project |
|-----------|-----------------------------------|
| Continuous Verification | `@login_required` на кожному view |
| Object-Level Permissions | `get_object_or_404(Note, pk=pk, user=request.user)` |
| Input Validation | `NoteForm.clean_*()`, `MinValueValidator` в моделях |
| Least Privilege | `user.groups.all()` фільтрація для Group sharing |
| Audit Logging | (для розширення) `django.security` logger |
| MFA | (для розширення) `django-two-factor-auth` |
