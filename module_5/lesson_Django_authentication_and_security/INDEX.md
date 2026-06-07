# Урок: Django Автентифікація та Безпека — Навігація

> **Проєкт:** `crispy_notes_project` — додаток для нотаток з повним auth-стеком та груповим доступом
>
> **Рівень:** Для студентів, що вже знайомі з базами Django (models, views, templates, forms)
>
> **Що вивчаємо:**
> - Аутентифікація та авторизація в Django
> - Сесії, cookies, login/logout потік
> - Password reset та зміна паролю
> - Захист об'єктів (IDOR prevention)
> - Групи для спільного доступу до нотаток
> - Налаштування безпеки Django
> - OWASP Top 10 та архітектура безпеки

---

## Рекомендований порядок вивчення

### Крок 1 — Теорія: Що таке безпека?
📄 **[SECURITY_FOUNDATIONS.md](SECURITY_FOUNDATIONS.md)**

CIA Triad, Trust Boundary, Attack Surface, Defense-in-Depth, хешування паролів, CSRF, Least Privilege.
Починай тут якщо ніколи не чув про кібербезпеку.

---

### Крок 2 — Аутентифікація в Django
📄 **[AUTH_BASICS.md](AUTH_BASICS.md)**

- Аутентифікація (хто ти?) vs Авторизація (що тобі можна?)
- Компоненти Django: `User`, `authenticate()`, `login()`, `logout()`
- Middleware — як Django "знає" хто надсилає запит
- `@login_required` — захист views
- Mermaid-діаграма: middleware lifecycle

---

### Крок 3 — Сесії та Login/Logout потік
📄 **[SESSIONS_FLOW.md](SESSIONS_FLOW.md)**

- Чому HTTP "не пам'ятає" юзера (stateless)
- Як cookies та sessions вирішують цю проблему
- Повний потік: Login → Cookie → Logout
- Mermaid sequence diagram
- Password Reset покроково
- URL-маршрутизація auth views

---

### Крок 4 — Дозволи та Групи
📄 **[PERMISSIONS.md](PERMISSIONS.md)**

- Що таке Permissions у Django (4 базових дозволи)
- Object-Level Permissions — захист конкретних об'єктів
- IDOR — Insecure Direct Object Reference (атака і захист)
- Групи для спільного доступу ("Сімя", "Робота")
- ER-діаграма: Юзер, Група, Нотатка

---

### Крок 5 — Типові помилки
📄 **[SECURITY_MISCONCEPTIONS.md](SECURITY_MISCONCEPTIONS.md)**

6 поширених хибних уявлень:
1. "Приховав кнопку = захистив"
2. "Якщо залогінений — може все"
3. "Тестую від суперюзера = все ОК"
4. "Глобальний queryset — нормально"
5. "Клієнтська валідація захищає"
6. "DEBUG=True в production — тимчасово"

---

### Крок 6 — Django Admin
📄 **[DJANGO_ADMIN.md](DJANGO_ADMIN.md)**

- Що таке `/admin/` і хто туди має доступ
- `is_staff` vs `is_superuser` — різниця
- `ModelAdmin` — налаштування списків та фільтрів
- Як призначити права через Admin
- `python manage.py createsuperuser`

---

### Крок 7 — Налаштування безпеки Django
📄 **[DJANGO_SECURITY_ARCHITECTURE.md](DJANGO_SECURITY_ARCHITECTURE.md)**

- Повний цикл обробки запиту (middleware pipeline)
- Хешування паролів (PBKDF2)
- ORM — захист від SQL Injection
- CSRF та XSS захист
- Безпека файлових завантажень
- Чек-ліст production налаштувань

---

### Крок 8 — OWASP Top 10
📄 **[OWASP_TOP_10.md](OWASP_TOP_10.md)**

10 найпоширеніших вразливостей вебзастосунків і як Django захищає від кожної:
A01 Broken Access Control → A10 SSRF

---

### Крок 9 — Zero Trust Architecture
📄 **[ZERO_TRUST.md](ZERO_TRUST.md)**

- "Never trust, always verify"
- 6 принципів: Continuous Verification, Least Privilege, IAM/MFA, Micro-segmentation, Monitoring
- Django реалізація кожного принципу з кодом

---

### Крок 10 — SIEM та Логування
📄 **[SIEM.md](SIEM.md)**

- Що таке SIEM (Security Information and Event Management)
- Django LOGGING конфігурація
- Які події логувати (brute-force, IDOR, audit trail)
- Rsyslog + Stunnel для передачі логів
- ELK Stack (Elasticsearch, Logstash, Kibana)

---

## Структура проєкту

```
crispy_notes_project/
├── hello_project/
│   ├── settings.py       ← security settings block + EMAIL_BACKEND
│   └── urls.py           ← include('django.contrib.auth.urls')
├── hello_app/
│   ├── models.py         ← Note.group FK, ShoppingList.group FK
│   ├── views.py          ← group views + PermissionDenied
│   ├── selectors.py      ← Q(user=user) | Q(group__in=user_groups)
│   ├── services.py       ← create_group, add_user_to_group
│   ├── forms.py          ← GroupCreateForm, GroupAddMemberForm
│   └── urls.py           ← /groups/ URL patterns
└── templates/
    ├── registration/
    │   ├── login.html                   ← + "Забули пароль?"
    │   ├── password_reset_form.html     ← форма email
    │   ├── password_reset_done.html     ← "перевір пошту"
    │   ├── password_reset_confirm.html  ← нова форма пароля
    │   ├── password_reset_complete.html ← успіх
    │   ├── password_reset_email.html    ← текст листа
    │   ├── password_change_form.html    ← зміна пароля
    │   └── password_change_done.html   ← успіх
    └── hello_app/
        ├── group_list.html
        ├── group_form.html
        ├── group_detail.html
        └── group_confirm_delete.html
```

---

## Quickstart

```bash
cd crispy_notes_project/

# Перший запуск:
python manage.py migrate
python manage.py createsuperuser  # для /admin/
python manage.py runserver

# Перевірити auth URLs:
# http://127.0.0.1:8000/accounts/login/
# http://127.0.0.1:8000/accounts/password_reset/
# http://127.0.0.1:8000/accounts/password_change/

# Перевірити групи:
# http://127.0.0.1:8000/groups/
# http://127.0.0.1:8000/groups/new/

# Перевірити Django конфіг:
python manage.py check
```
