# Django Admin + Unfold — Архітектура внутрішніх інструментів

> Django Admin — це вбудований адмін-інтерфейс для управління моделями.
> Unfold — сучасний UI-шар поверх нього на Tailwind CSS.
> Цей файл охоплює стандартну адмінку Django і повну систему Unfold
> від базового налаштування до enterprise-архітектури.

---

## Зміст


- [0. Що таке Django Admin і навіщо Unfold](#0-що-таке-django-admin-і-навіщо-unfold)
- [1. AdminSite — координатор інтерфейсу](#1-adminsite--координатор-інтерфейсу)
- [2. ModelAdmin — CRUD-генератор](#2-modeladmin--crud-генератор)
- [3. Admin Request Lifecycle — від HTTP до БД](#3-admin-request-lifecycle--від-http-до-бд)
- [4. ChangeList — рушій списків](#4-changelist--рушій-списків)
- [5. Query Architecture — оптимізація запитів](#5-query-architecture--оптимізація-запитів)
- [6. Admin Rendering Pipeline — шаблони і TemplateResponse](#6-admin-rendering-pipeline--шаблони-і-templateresponse)
- [7. Unfold — встановлення і базова конфігурація](#7-unfold--встановлення-і-базова-конфігурація)
- [8. Sidebar + Navigation Architecture](#8-sidebar--navigation-architecture)
- [9. Dashboard — layouts і DASHBOARD_CALLBACK](#9-dashboard--layouts-і-dashboard_callback)
- [10. Widget Systems — Card, Chart, Tracker, Cohort](#10-widget-systems--card-chart-tracker-cohort)
- [11. Information Hierarchy — Fieldset tabs, Conditional fields](#11-information-hierarchy--fieldset-tabs-conditional-fields)
- [12. Enterprise Patterns — паралельний UnfoldAdminSite, InfinitePaginator](#12-enterprise-patterns--паралельний-unfoldadminsite-infinitepaginator)
- [13. Admin Anti-Patterns](#13-admin-anti-patterns)
- [14. Питання для самоперевірки](#14-питання-для-самоперевірки)
- [15. Advanced Filtering — AutocompleteSelectFilter, RangeDateTimeFilter](#15-advanced-filtering--autocompleteselectfilter-rangedatetimefilter)
- [16. Bulk Actions і Dialog Actions — BaseDialogForm](#16-bulk-actions-і-dialog-actions--basedialogform)
- [17. Component Classes — @register_component](#17-component-classes--register_component)
- [18. Custom Pages — UnfoldModelAdminViewMixin](#18-custom-pages--unfoldmodeladminviewmixin)
- [19. Advanced Widgets — WysiwygWidget, ArrayWidget](#19-advanced-widgets--wysiwygwidget-arraywidget)
- [20. Performance і Caching — cached.Loader, full-text search, Redis](#20-performance-і-caching--cachedloader-full-text-search-redis)
- [21. Datasets — пов'язані записи у ChangeForm](#21-datasets--повязані-записи-у-changeform)
- [22. Production Checklist](#22-production-checklist)

---
- **🧠 Ментальна модель:** Django Admin — це LEGO-конструктор для внутрішніх інструментів. Кожна модель (Note, Category, User) — це набір деталей. Django автоматично будує з них повноцінний CRUD-інтерфейс: список, форму додавання, форму редагування, видалення. Unfold — це новий набір "лего" поверх старого: ті ж деталі, але сучасний дизайн і нові компоненти.
- **📚 Чому це існує:** До Django Admin, кожен проект мав самостійно будувати адмін-панель: HTML-форми, валідацію, права доступу, пагінацію. Django Admin вирішив цю проблему раз і назавжди — автоматичний CRUD для будь-якої зареєстрованої моделі, з правами, аудитом і пошуком з коробки. Unfold вирішив проблему застарілого Bootstrap 3 UI — без зміни бізнес-логіки.
- **🌐 Що відбувається під капотом:** При запуску Django, `apps.py` кожного встановленого додатку виконується. `admin.autodiscover()` знаходить і завантажує `admin.py` у кожному додатку. Кожен `admin.site.register(Model, ModelAdmin)` реєструє модель у глобальному `AdminSite` синглтоні. При запиті до `/admin/` Django викликає `AdminSite.urls`, який динамічно генерує URL-маршрути для всіх зареєстрованих моделей.
- **❌ Типова помилка початківця:** Думати, що Django Admin — це для кінцевих користувачів. Адмінка призначена ВИКЛЮЧНО для внутрішньої команди: адміністраторів, редакторів, підтримки. Зовнішні користувачі повинні мати окремий інтерфейс на звичайних Django Views + Bootstrap. Використання адмінки як "фронтенду" — анти-патерн.
---

## Орієнтація: Як читати цей документ

Перш ніж занурюватись у секції — зрозумій загальну архітектурну картину:

```
Весь Django Admin — це три шари поверх один одного:

┌─────────────────────────────────────────────────────┐
│                 Твій код                            │
│   ModelAdmin, actions, inlines, custom views        │
│   (§2, §4, §11, §16–18)                             │
├─────────────────────────────────────────────────────┤
│               Unfold Layer                          │
│   Tailwind UI, Dashboard, Sidebar, Components       │
│   (§7–12, §15–21)                                   │
├─────────────────────────────────────────────────────┤
│           django.contrib.admin                      │
│   AdminSite, ModelAdmin base, ChangeList, ORM       │
│   (§1–6)                                            │
├─────────────────────────────────────────────────────┤
│           Django Core                               │
│   ORM, Template Engine, Middleware, Auth            │
└─────────────────────────────────────────────────────┘
```

**Порядок читання для початківців:**

1. [§0 → загальна картина, навіщо взагалі Admin](#0-що-таке-django-admin-і-навіщо-unfold)
2. [§3 → Request Lifecycle (розумієш як Django обробляє запит до адмінки)](#3-admin-request-lifecycle--від-http-до-бд)
3. [§2 → ModelAdmin (основний інструмент, 80% часу тут)](#2-modeladmin--crud-генератор)
4. [§5 → Query Architecture (N+1 — найпоширеніша проблема)](#5-query-architecture--оптимізація-запитів)
5. [§7 → Unfold встановлення (після розуміння основ)](#7-unfold--встановлення-і-базова-конфігурація)
6. [§9 → Dashboard (перша "вау" фіча)](#9-dashboard--layouts-і-dashboard_callback)
7. [§13 → Anti-Patterns (читай до написання production коду)](#13-admin-anti-patterns)
8. [§22 → Checklist (перед деплоєм)](#21-datasets--повязані-записи-у-changeform)

---

## §0. Що таке Django Admin і навіщо Unfold

### Django Admin — вбудований CRUD

Django автоматично генерує повноцінний адмін-інтерфейс для кожної зареєстрованої моделі:

```
URL /admin/  →  Список додатків + моделей
              →  Список записів (ChangeList)
              →  Форма редагування (ChangeForm)
              →  Форма додавання
              →  Видалення з підтвердженням
```

```python
# hello_app/admin.py — мінімальна реєстрація
from django.contrib import admin
from .models import Note

admin.site.register(Note)
# → /admin/hello_app/note/          список нотаток
# → /admin/hello_app/note/add/      нова нотатка
# → /admin/hello_app/note/42/change/ редагування
# → /admin/hello_app/note/42/delete/ видалення
```

### Проблема стандартної адмінки

```
Стандартна Django Admin          Unfold Admin
─────────────────────────        ─────────────
Базовий Bootstrap 3 стиль   →   Tailwind CSS з темною темою
Плоский список моделей       →   Sidebar з ієрархією і іконками
Немає дашборду              →   Кастомна сторінка з Chart.js
Немає command palette        →   Глобальний пошук (Ctrl+K)
Прості текстові фільтри     →   Dropdown + date range фільтри
Немає WYSIWYG               →   TipTap / CKEditor 5 інтеграція
Немає умовних полів         →   Alpine.js conditional fields
```

### Ключова філософія Unfold

Unfold **не замінює** `django.contrib.admin` — він розширює його.
Всі стандартні API (`ModelAdmin`, `list_display`, `inlines`) працюють без змін.
Unfold додає сучасний UI поверх існуючої архітектури.

```
django.contrib.admin  (архітектура, ORM, permissions)
        ↑
    Unfold           (Tailwind UI, компоненти, dashboard)
        ↑
  Ваш ModelAdmin    (бізнес-логіка, кастомізація)
```

---

---
- **🧠 Ментальна модель:** `AdminSite` — це "головний офіс" твоєї адмін-панелі. Всі моделі "реєструються" в ньому як "відділи". Він контролює URL-маршрутизацію (які URL доступні), брендинг (назва, логотип), і права доступу (хто може увійти). Без `AdminSite` — немає адмінки. Один проект може мати кілька `AdminSite` — наприклад, окремий для операційної команди і окремий для аналітиків.
- **📚 Чому це існує:** `AdminSite` — це Singleton (єдиний екземпляр). Django створює `admin.site` автоматично при старті. Тобі не потрібно його створювати — лише налаштовувати. Але якщо потрібна ізоляція (різні команди бачать різні моделі) — можна створити додаткові `AdminSite`. Це enterprise-паттерн для великих команд.
- **🌐 Що відбувається під капотом:** `admin.site.register(Note)` додає клас `NoteAdmin` у внутрішній словник `_registry: {Note: NoteAdmin}`. Коли Django обробляє запит `/admin/hello_app/note/`, він шукає Note в `_registry`, отримує `NoteAdmin`, і делегує обробку йому. `each_context()` викликається при КОЖНОМУ запиті до адмінки і додає глобальні змінні (назва сайту, права, повідомлення) у контекст шаблону.
- **❌ Типова помилка початківця:** Намагатися змінити `site_header` через `UNFOLD` settings і не бачити змін — бо модуль `unfold` не стоїть першим у `INSTALLED_APPS`. Або реєструвати модель двічі: один раз через `admin.site.register()` і ще раз через `@admin.register()` — це викличе `AlreadyRegistered` виключення.
---

## §1. AdminSite — координатор інтерфейсу

### Що таке AdminSite

`AdminSite` — синглтон, що управляє:
- Реєстрацією моделей (`register()`)
- URL-маршрутизацією (`/admin/*`)
- Глобальним брендингом (`site_header`, `site_title`)
- Контекстом шаблонів (`each_context()`)

```python
# Django автоматично створює глобальний екземпляр
from django.contrib import admin

admin.site.site_header = 'Bootstrap Notes Admin'
admin.site.site_title = 'Notes Portal'
admin.site.index_title = 'Управління нотатками'
```

### Кілька AdminSite для різних ролей

```python
# hello_app/admin_sites.py

from django.contrib.admin import AdminSite

class OperationsAdminSite(AdminSite):
    """Адмін-панель для операційної команди."""
    site_header = 'Operations Panel'
    site_title = 'Ops'
    index_title = 'Операційний дашборд'

class AnalyticsAdminSite(AdminSite):
    """Read-only аналітична панель."""
    site_header = 'Analytics'
    site_title = 'Analytics'

    def has_permission(self, request):
        # Тільки staff, але без is_superuser вимоги
        return request.user.is_active and request.user.is_staff


operations_admin = OperationsAdminSite(name='operations')
analytics_admin = AnalyticsAdminSite(name='analytics')
```

```python
# urls.py
from hello_app.admin_sites import operations_admin, analytics_admin

urlpatterns = [
    path('admin/', admin.site.urls),               # стандартний
    path('ops/', operations_admin.urls),            # операційний
    path('analytics/', analytics_admin.urls),       # аналітичний
]
```

```python
# hello_app/admin.py — реєстрація на кількох сайтах
from hello_app.admin_sites import operations_admin, analytics_admin

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at']

# Додаткова реєстрація на operations_admin
operations_admin.register(Note, NoteAdmin)
analytics_admin.register(Note, NoteAdmin)
```

### each_context() — ін'єкція глобальних змінних

```python
class CustomAdminSite(AdminSite):
    def each_context(self, request):
        context = super().each_context(request)
        # Додаємо глобальні змінні для всіх шаблонів цього сайту
        context.update({
            'company_name': 'Acme Corp',
            'environment': settings.ENVIRONMENT,
            'unread_alerts': SystemAlert.objects.filter(read=False).count(),
        })
        return context
```

---

---
- **🧠 Ментальна модель:** `ModelAdmin` — це декларативний "рецепт" для автоматичного CRUD. Як у поварській книзі: ти описуєш ЩО хочеш (`list_display = ['title', 'author']`), а Django сам готує (генерує SQL, HTML, форми, пагінацію). Ти не пишеш жодного HTML — тільки Python-атрибути. Клас `ModelAdmin` є СИНГЛТОНОМ — один екземпляр обслуговує всі запити всіх користувачів одночасно. Це критично для розуміння анти-патернів.
- **📚 Чому це існує:** ModelAdmin відокремлює "що показувати" від "як показувати". Модель знає про дані (поля, валідацію, зв'язки). ModelAdmin знає про адмін-UX: які поля в списку, які фільтри, які дії. Якщо завтра дизайн адмінки зміниться — ти правиш ModelAdmin, а не модель. Якщо бізнес-логіка зміниться — ти правиш модель, а не ModelAdmin.
- **🌐 Що відбувається під капотом:** При запиті до `/admin/hello_app/note/` Django: (1) знаходить `NoteAdmin` в `_registry`, (2) викликає `NoteAdmin.changelist_view(request)`, (3) цей метод викликає `get_queryset()`, `get_list_display()`, `get_list_filter()`, збирає контекст, (4) повертає `TemplateResponse('admin/change_list.html', context)`. Кожен атрибут (`list_display`, `search_fields` тощо) — це "інструкція" для відповідного методу.
- **❌ Типова помилка початківця:** Мутувати клас-атрибути в методах: `self.readonly_fields.append('title')` — змінює поле для ВСІХ запитів і ВСІХ користувачів одночасно (бо ModelAdmin — синглтон). Завжди повертай нові списки: `return list(self.readonly_fields) + ['title']`. Ця помилка — одна з найважчих для діагностики (баг з'являється під навантаженням або у concurrency).
---

## §2. ModelAdmin — CRUD-генератор

### Декларативна конфігурація

```python
# hello_app/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Note, Category

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):

    # ── Список записів ────────────────────────────────────────
    list_display = ['title', 'status_badge', 'author', 'category', 'created_at']
    list_display_links = ['title']      # клікабельні поля
    list_editable = ['category']        # редагування прямо в списку
    list_filter = ['status', 'category', 'created_at']
    list_per_page = 25
    list_select_related = ['author', 'category']  # уникнення N+1
    search_fields = ['title', 'body', 'author__username']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'       # навігація по датах

    # ── Форма редагування ─────────────────────────────────────
    fields = ['title', 'body', 'category', 'status', 'is_public']
    # або fieldsets для групування:
    fieldsets = [
        ('Основна інформація', {
            'fields': ['title', 'category', 'status'],
        }),
        ('Зміст', {
            'fields': ['body'],
        }),
        ('Налаштування', {
            'fields': ['is_public', 'author'],
            'classes': ['collapse'],    # згортається за замовчуванням
        }),
    ]
    readonly_fields = ['created_at', 'updated_at', 'slug']
    autocomplete_fields = ['author']    # пошук через AJAX (потрібен search_fields на UserAdmin)
    raw_id_fields = []

    # ── Дії ───────────────────────────────────────────────────
    actions = ['publish_selected', 'archive_selected']

    # ── Inline ────────────────────────────────────────────────
    inlines = []  # додається нижче

    # ── Кастомне поле для list_display ───────────────────────
    @admin.display(description='Статус', ordering='status')
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'published': '#198754',
            'archived': '#ffc107',
        }
        color = colors.get(obj.status, '#0d6efd')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:12px;">{}</span>',
            color,
            obj.get_status_display()
        )

    # ── Дії ───────────────────────────────────────────────────
    @admin.action(description='Опублікувати вибрані')
    def publish_selected(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'Опубліковано {updated} нотаток.')

    @admin.action(description='Архівувати вибрані')
    def archive_selected(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(
            request,
            f'Архівовано {updated} нотаток.',
            level='warning'
        )
```

### Динамічна конфігурація через перевизначення методів

```python
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        """Обмежуємо відображення — кожен бачить тільки свої нотатки."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(author=request.user)

    def get_readonly_fields(self, request, obj=None):
        """Поле author тільки для читання при редагуванні."""
        if obj:  # existing object
            return self.readonly_fields + ('author',)
        return self.readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        """Динамічна форма залежно від ролі."""
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            # Ховаємо поле is_public для звичайних адмінів
            form.base_fields.pop('is_public', None)
        return form

    def save_model(self, request, obj, form, change):
        """Автоматично встановлюємо author при створенні."""
        if not change:  # новий об'єкт
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        """Видалення тільки для суперюзерів."""
        return request.user.is_superuser
```

### Inline — вкладені форми

```python
class CommentInline(admin.TabularInline):
    model = Comment
    fields = ['author', 'text', 'created_at']
    readonly_fields = ['created_at']
    extra = 1           # кількість порожніх форм
    max_num = 10
    can_delete = True
    show_change_link = True  # посилання на повну форму Comment


class AttachmentInline(admin.StackedInline):
    model = Attachment
    fields = ['file', 'description']
    extra = 0


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    inlines = [CommentInline, AttachmentInline]
```

### Кастомні URL у ModelAdmin

```python
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/export/',
                self.admin_site.admin_view(self.export_view),  # ← обов'язково
                name='hello_app_note_export',
            ),
        ]
        return custom_urls + urls

    def export_view(self, request, pk):
        note = get_object_or_404(Note, pk=pk)
        # ... генерація PDF або CSV
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename=note_{pk}.txt'
        response.write(note.body)
        return response
```

```html
{# templates/admin/hello_app/note/change_form.html #}
{% extends "admin/change_form.html" %}
{% block object-tools-items %}
{{ block.super }}
<li>
    <a href="{% url 'admin:hello_app_note_export' original.pk %}"
       class="historylink">Експорт у .txt</a>
</li>
{% endblock %}
```

---

---
- **🧠 Ментальна модель:** Admin Request Lifecycle — це конвеєр. Кожен запит до `/admin/note/42/change/` проходить через фіксовану послідовність "станцій": автентифікація → авторизація → отримання об'єкта → перевірка прав → рендеринг форми (GET) або валідація + збереження (POST). Якщо будь-яка станція "відмовляє" — конвеєр зупиняється і повертає відповідну відповідь (403, 404, форму з помилками).
- **📚 Чому це існує:** Lifecycle чітко розділяє відповідальність: middleware не знає про моделі, ModelAdmin не знає про HTTP-деталі. Ти можеш перехопити будь-яку "станцію" конвеєра: `get_form()` — для зміни форми, `save_model()` — для зміни логіки збереження, `response_change()` — для зміни редиректу. Не потрібно переписувати все — тільки override потрібної станції.
- **🌐 Що відбувається під капотом:** `has_change_permission()` виконує SQL-запит для перевірки прав (через `ContentType` фреймворк). `get_form()` динамічно генерує `ModelForm` клас на льоту. `save_model()` викликає `obj.full_clean()` (валідація полів) а потім `obj.save()` (INSERT або UPDATE в БД). `log_change()` записує рядок в таблицю `django_admin_log` — це вбудований аудит-лог.
- **❌ Типова помилка початківця:** Виконувати дорогі операції (відправка email, виклик зовнішнього API) прямо в `save_model()` без try/except. Якщо email-сервер недоступний — адмінка "падає" при спробі збереження. Важкі side effects кращe виконувати в Celery task, який запускається з `save_model()`.
---

## §3. Admin Request Lifecycle

```
HTTP Request /admin/hello_app/note/42/change/
    │
    ▼
Middleware stack:
    SessionMiddleware    → завантажує сесію
    AuthenticationMiddleware → request.user
    MessageMiddleware   → Django messages framework
    │
    ▼
AdminSite.urls dispatch
    │
    ▼
ModelAdmin.change_view(request, object_id)
    │
    ├─ has_change_permission(request, obj) → 403 якщо False
    │
    ├─ GET:
    │     get_form() → ModelForm instance
    │     get_readonly_fields()
    │     get_fieldsets()
    │     render TemplateResponse('admin/change_form.html', context)
    │
    └─ POST:
          get_form() з request.POST
          form.is_valid()
              ├─ False: рендерити форму з помилками
              └─ True:
                    save_model(request, obj, form, change)
                        → obj.save()
                    save_related(request, form, formsets, change)
                        → зберегти inlines
                    log_change() → LogEntry
                    response_change() → HttpResponseRedirect
```

### Перехоплення збереження

```python
def save_model(self, request, obj, form, change):
    """Виконується безпосередньо перед obj.save()."""
    if not change:
        obj.created_by = request.user
    obj.last_modified_by = request.user
    super().save_model(request, obj, form, change)

def save_related(self, request, form, formsets, change):
    """Виконується після save_model, зберігає M2M і inlines."""
    super().save_related(request, form, formsets, change)
    # Тут obj вже збережений з ID
    obj = form.instance
    obj.process_tags()  # наприклад

def response_change(self, request, obj):
    """Контроль редиректу після успішного збереження."""
    if '_continue' not in request.POST and '_addanother' not in request.POST:
        # Власний редирект замість стандартного
        return redirect(reverse('admin:hello_app_note_changelist'))
    return super().response_change(request, obj)
```

---

---
- **🧠 Ментальна модель:** `ChangeList` — це "менеджер списків". Якщо `ModelAdmin` — це рецепт, то `ChangeList` — це кухар, який готує список об'єктів: застосовує фільтри, сортування, пагінацію, пошук. Django автоматично створює екземпляр `ChangeList` при кожному запиті до списку. Якщо хочеш змінити поведінку списку — створи підклас `ChangeList` і перевизнач потрібні методи.
- **📚 Чому це існує:** `ChangeList` відокремлює "логіку відображення списку" від "відображення форми редагування". Це дозволяє незалежно оптимізувати кожну частину: швидкий список → агрегації і индекси; повільна форма → не проблема для списку. `ShowFacets` (Django 5.0+) — конкретний приклад: додає `COUNT(*)` для кожного фільтра, щоб показати скільки записів відповідає.
- **🌐 Що відбувається під капотом:** `ChangeList.get_queryset()` будує queryset поетапно: (1) бере базовий queryset від `ModelAdmin.get_queryset()`, (2) застосовує `search_fields` (додає `WHERE title ILIKE '%query%'`), (3) застосовує `list_filter` (додає `WHERE status='draft'`), (4) застосовує `date_hierarchy` (WHERE created_at BETWEEN ...), (5) застосовує сортування (`ORDER BY`), (6) обрізає для пагінації (`LIMIT/OFFSET`). Кожен крок — окремий `.filter()` або `.order_by()` на QuerySet.
- **❌ Типова помилка початківця:** Додавати `annotate()` у `ModelAdmin.get_queryset()` але забути додати відповідне поле у `list_display` через кастомний метод з `@admin.display(ordering='annotated_field')`. Без `ordering` на колонці — клік по заголовку колонки не сортуватиме.
---

## §4. ChangeList — рушій списків

```python
from django.contrib.admin.views.main import ChangeList

class NoteChangeList(ChangeList):
    """Кастомний ChangeList з додатковою агрегацією."""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Annotate для використання в list_display
        from django.db.models import Count
        return qs.annotate(comments_count=Count('comments'))


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):

    def get_changelist(self, request, **kwargs):
        return NoteChangeList

    @admin.display(description='Коментарі', ordering='comments_count')
    def comments_count(self, obj):
        return obj.comments_count
```

### Show Facets (Django 5.0+)

```python
from django.contrib.admin import ModelAdmin, ShowFacets

@admin.register(Note)
class NoteAdmin(ModelAdmin):
    list_filter = ['status', 'category']
    show_facets = ShowFacets.ALWAYS
    # → біля кожного фільтра показує "(23)" — кількість записів
    # ShowFacets.ALLOW (за запитом) | ShowFacets.ALWAYS | ShowFacets.NEVER
```

---

---
- **🧠 Ментальна модель:** N+1 проблема в адмінці — це "ефект сніжної кулі". Для сторінки зі списком 25 нотаток Django виконує 1 запит для самих нотаток, а потім ще 25 запитів для авторів і ще 25 для категорій — разом 51 запит замість 1. `list_select_related` — це "зупинити сніжну кулю": одним `JOIN` отримати все разом. Це найлегша оптимізація з найбільшим ефектом у Django Admin.
- **📚 Чому це існує:** QuerySet в Django — ледачий (lazy). `note.author` не виконує SQL відразу — він очікує на перший доступ. Коли шаблон рендерить `{{ note.author.username }}` для кожної нотатки — виконується окремий SQL. `select_related` і `prefetch_related` кажуть ORM: "зроби JOIN заздалегідь, я знаю що буду звертатися до цих даних".
- **🌐 Що відбувається під капотом:** `list_select_related = ['author', 'category']` → Django додає `SELECT notes.*, users.*, categories.* FROM notes LEFT JOIN users ON ... LEFT JOIN categories ON ...`. Один SQL замість 1+N. `prefetch_related('tags')` — для M2M не можна JOIN (дублювання рядків), тому Django виконує два SQL: один для нотаток, один для тегів, і Python об'єднує їх у пам'яті.
- **❌ Типова помилка початківця:** `list_select_related = True` (без списку) — Django робить JOIN для ВСІХ ForeignKey у всіх глибинах. Для складних моделей це може бути повільніше ніж N+1. Завжди явно вказуй які поля потрібні: `list_select_related = ['author', 'category']`.
---

## §5. Query Architecture

### N+1 у list_display

```python
# ❌ N+1 — для кожної нотатки окремий запит на author і category
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_name', 'category_name']

    def author_name(self, obj):
        return obj.author.username  # SELECT author WHERE id=...

    def category_name(self, obj):
        return obj.category.name    # SELECT category WHERE id=...

# ✅ Виправлення через list_select_related
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_name', 'category_name']
    list_select_related = ['author', 'category']  # JOIN в одному запиті

    def author_name(self, obj):
        return obj.author.username  # вже в кеші

    def category_name(self, obj):
        return obj.category.name    # вже в кеші
```

### Оптимізація search_fields

```python
# ❌ Небезпечний пошук — LIKE на TEXT полі + FK traversal
search_fields = ['body', 'author__profile__bio']
# → WHERE body LIKE '%query%' OR profile.bio LIKE '%query%'
# → Full scan на великих таблицях + JOIN

# ✅ Безпечний пошук
search_fields = ['^title', '=author__username']
# ^ — startswith (використовує індекс!)
# = — exact match
# @ — full-text search (тільки MySQL/PostgreSQL)
# (без префікса) — icontains (повільно, але flexible)
```

### get_search_results() — кастомний пошук

```python
def get_search_results(self, request, queryset, search_term):
    queryset, use_distinct = super().get_search_results(
        request, queryset, search_term
    )
    # Додаємо пошук по тегах
    if search_term:
        queryset |= self.model.objects.filter(
            tags__name__icontains=search_term
        )
    return queryset, use_distinct
```

### prefetch_related для M2M в list_display

```python
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'tag_list']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return ', '.join(tag.name for tag in obj.tags.all())
    tag_list.short_description = 'Теги'
```

---

---
- **🧠 Ментальна модель:** Admin Rendering Pipeline — це фотозбірник. `ModelAdmin.changelist_view()` збирає "фотографії" (context: queryset, фільтри, пагінацію), але ще не друкує їх. `TemplateResponse` зберігає ці "фотографії" у незрендерованому стані. Middleware може додати свої "фотографії" до альбому. Тільки наприкінці Django "друкує" готову книжку (компілює HTML).
- **📚 Чому це існує:** Ієрархія шаблонів дозволяє override на різних рівнях деталізації: хочеш змінити щось для ВСІХ моделей — правиш `templates/admin/change_list.html`. Хочеш змінити для всіх моделей конкретного додатку — правиш `templates/admin/hello_app/change_list.html`. Хочеш змінити тільки для `Note` — правиш `templates/admin/hello_app/note/change_list.html`. Django шукає від найспецифічнішого до найзагальнішого.
- **🌐 Що відбувається під капотом:** Django Template Engine при рендерингу адмін-шаблону запитує `TemplateEngine.select_template(['admin/hello_app/note/change_list.html', 'admin/hello_app/change_list.html', 'admin/change_list.html'])`. Він перевіряє файлову систему для кожного варіанту по черзі і повертає перший знайдений. Це відбувається при КОЖНОМУ запиті (або з кешу при `cached.Loader`).
- **❌ Типова помилка початківця:** Створити файл `templates/admin/change_list.html` з власним контентом і забути написати `{% extends "admin/change_list.html" %}` всередині — Django прочитає ТВІЙ файл (найбільш специфічний) і не знайде жодної базової структури. Адмінка відображатиме порожню сторінку або ламатиметься. ЗАВЖДИ `{% extends %}` + `{% block %}` + `{{ block.super }}`.
---

## §6. Admin Rendering Pipeline

### TemplateResponse і пізня компіляція

```
ModelAdmin.changelist_view()
    │
    └─ return TemplateResponse(
           request,
           'admin/change_list.html',
           context
       )
           │
           │  ← Response middleware може змінити context_data тут
           │
           ▼
    TemplateResponse.render()  (викликається Django)
           │
           └─ Template Engine → HTML string → HttpResponse
```

```python
def changelist_view(self, request, extra_context=None):
    # Додаємо кастомний контекст
    extra_context = extra_context or {}
    extra_context['total_published'] = Note.objects.filter(
        status='published'
    ).count()
    return super().changelist_view(request, extra_context=extra_context)
```

### Ієрархія шаблонів

```
Django шукає шаблони в такому порядку:
1. templates/admin/<app>/<model>/change_list.html    (найспецифічніший)
2. templates/admin/<app>/change_list.html
3. templates/admin/change_list.html                  (глобальний)
4. django/contrib/admin/templates/admin/change_list.html (вбудований)

Приклад для Note:
templates/
└── admin/
    ├── base_site.html            ← глобальний брендинг
    ├── change_list.html          ← для всіх моделей
    └── hello_app/
        ├── change_list.html      ← для всіх моделей hello_app
        └── note/
            ├── change_list.html  ← тільки для Note
            └── change_form.html
```

```html
{# templates/admin/base_site.html — ребрендинг адмінки #}
{% extends "admin/base.html" %}

{% block branding %}
<h1 id="site-name">
    <a href="{% url 'admin:index' %}">
        🗒️ {{ site_header }}
    </a>
</h1>
{% endblock %}

{% block extrastyle %}
{{ block.super }}
<style>
    #header { background: #1e293b; }
    .module h2 { background: #334155; }
</style>
{% endblock %}
```

---

---
- **🧠 Ментальна модель:** Встановлення Unfold — це "косметичний ремонт" Django Admin. Ти не зносиш стіни (не змінюєш ModelAdmin, ORM, права доступу) — ти лише фарбуєш стіни і міняєш меблі (CSS/JS шаблони). Весь код `ModelAdmin` який ти написав — продовжує працювати. Unfold просто замінює шаблони і стилі поверх.
- **📚 Чому `unfold` ПЕРШИЙ у `INSTALLED_APPS`:** Django шукає шаблони в `INSTALLED_APPS` по порядку. Якщо `unfold` стоїть після `django.contrib.admin` — Django знаходить стандартні admin шаблони першими і НІКОЛИ не доходить до Unfold шаблонів. `unfold` ПОВИНЕН бути першим, щоб його шаблони мали пріоритет над стандартними.
- **🌐 Що відбувається під капотом:** Unfold замінює стандартні admin шаблони своїми (у своїй `templates/admin/` директорії). Його шаблони розширюють (`{% extends %}`) оригінальні Django admin шаблони і перевизначають CSS/JS блоки для підключення Tailwind CSS. `UnfoldModelAdmin` (підклас `ModelAdmin`) додає нові атрибути (`list_fullwidth`, `warn_unsaved_form` тощо), але не ламає стандартні.
- **❌ Типова помилка початківця:** Встановити Unfold але не перемкнути `ModelAdmin` на `UnfoldModelAdmin`. Базові стилі зміняться (бо шаблони Unfold завантажаться), але нові функції (`list_filter_submit`, `warn_unsaved_form`) не працюватимуть — вони реалізовані в `UnfoldModelAdmin`, а не в стандартному `ModelAdmin`.
---

## §7. Unfold — встановлення і базова конфігурація

### Встановлення

```bash
pip install django-unfold
```

```python
# settings.py — Unfold ПЕРЕД django.contrib.admin
INSTALLED_APPS = [
    'unfold',                       # ← обов'язково перший
    'unfold.contrib.filters',       # розширені фільтри
    'unfold.contrib.forms',         # стилізовані форми
    'unfold.contrib.inlines',       # сортовані inlines
    'unfold.contrib.import_export', # якщо використовуєте django-import-export

    'django.contrib.admin',
    'django.contrib.auth',
    ...
]
```

### Базова конфігурація UNFOLD

```python
# settings.py

from django.templatetags.static import static
from django.urls import reverse_lazy
from unfold.enums import BadgeType

UNFOLD = {
    # ── Брендинг ──────────────────────────────────────────────
    "SITE_TITLE": "Bootstrap Notes",
    "SITE_HEADER": "Notes Admin",
    "SITE_URL": "/",
    "SITE_ICON": lambda request: static("hello_app/img/logo.png"),
    "SITE_LOGO": lambda request: static("hello_app/img/logo-full.png"),
    "SITE_SYMBOL": "notes",             # Material Symbol іконка

    # ── Кольори (CSS змінні) ───────────────────────────────────
    "COLORS": {
        "primary": {
            "50": "240 249 255",        # RGB без #
            "100": "224 242 254",
            "500": "14 165 233",        # --un-color-primary-500
            "900": "12 74 110",
        },
    },

    # ── Теми ──────────────────────────────────────────────────
    "THEME": "dark",                    # "dark" | "light" | None (авто)

    # ── Dashboard ─────────────────────────────────────────────
    "DASHBOARD_CALLBACK": "hello_app.admin_dashboard.dashboard_callback",

    # ── Sidebar навігація ─────────────────────────────────────
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Нотатки",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Всі нотатки",
                        "icon": "description",
                        "link": reverse_lazy("admin:hello_app_note_changelist"),
                        "badge": "hello_app.admin_callbacks.get_draft_count",
                        "badge_type": BadgeType.WARNING,
                    },
                    {
                        "title": "Категорії",
                        "icon": "label",
                        "link": reverse_lazy("admin:hello_app_category_changelist"),
                    },
                ],
            },
            {
                "title": "Користувачі",
                "separator": True,
                "items": [
                    {
                        "title": "Користувачі",
                        "icon": "people",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                ],
            },
        ],
    },

    # ── Глобальне dropdown-меню ───────────────────────────────
    "SITE_DROPDOWN": [
        {
            "icon": "diamond",
            "title": "Продакшн",
            "link": "https://notes.example.com",
        },
        {
            "icon": "code",
            "title": "Staging",
            "link": "https://staging.notes.example.com",
        },
    ],

    # ── Tabs (вкладки для форм і списків) ─────────────────────
    "TABS": [
        {
            "models": ["hello_app.note", "hello_app.comment"],
            "items": [
                {
                    "title": "Нотатки",
                    "icon": "description",
                    "link": reverse_lazy("admin:hello_app_note_changelist"),
                },
                {
                    "title": "Коментарі",
                    "icon": "comment",
                    "link": reverse_lazy("admin:hello_app_comment_changelist"),
                },
            ],
        },
    ],
}
```

### UnfoldModelAdmin — базовий клас Unfold

```python
# hello_app/admin.py
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from django.contrib import admin
from .models import Note


@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    # Всі стандартні атрибути Django Admin працюють
    list_display = ['title', 'status', 'author', 'created_at']
    list_filter = ['status', 'category']
    search_fields = ['^title', '=author__username']

    # Unfold-специфічні атрибути
    list_fullwidth = True           # список на повну ширину
    warn_unsaved_form = True        # попередження при виході без збереження
    list_filter_submit = True       # кнопка "Застосувати" у фільтрах
```

---

---
- **🧠 Ментальна модель:** Sidebar навігація в Unfold — це "меню ресторану" яке ти пишеш вручну у `settings.py`. Стандартна Django Admin автоматично генерує меню з усіх зареєстрованих моделей (як "шведський стіл" — все підряд). Unfold дозволяє вручну організувати навігацію: групи, іконки, значки-лічильники (badges), колапсовані секції. Повний контроль за ціну більшої конфігурації.
- **📚 Чому `reverse_lazy` а не `reverse`:** Sidebar конфігурація у `settings.py` виконується при завантаженні модуля — до того як Django повністю ініціалізував URL-маршрути. `reverse('admin:hello_app_note_changelist')` в цей момент викине `NoReverseMatch`. `reverse_lazy` — це "відкладений reverse", який виконується тільки при першому зверненні (вже після повної ініціалізації).
- **🌐 Що відбувається під капотом:** Sidebar badge callback (`"hello_app.admin_callbacks.get_draft_count"`) — це рядковий шлях до Python-функції. Unfold динамічно імпортує і викликає цю функцію при КОЖНОМУ рендерингу сайдбару (при кожному запиті). Якщо badge callback повільний (складний SQL) — він уповільнить кожну сторінку адмінки. Кешуй результат якщо можливо.
- **❌ Типова помилка початківця:** Писати `"link": reverse("admin:hello_app_note_changelist")` (без `_lazy`) у `settings.py` на рівні модуля — і отримувати `ImproperlyConfigured: The included URLconf ... does not appear to have any patterns`. Завжди `reverse_lazy` у `settings.py`, `UNFOLD` словнику, і будь-якому місці де URL генерується до повного завантаження Django.
---

## §8. Sidebar + Navigation Architecture

### Динамічний badge через callback

```python
# hello_app/admin_callbacks.py

def get_draft_count(request):
    """Повертає кількість чернеток для badge у sidebar."""
    from .models import Note
    count = Note.objects.filter(status='draft').count()
    if count == 0:
        return None
    return str(count)
```

```python
# settings.py — UNFOLD → SIDEBAR → items
{
    "title": "Нотатки",
    "icon": "description",
    "link": reverse_lazy("admin:hello_app_note_changelist"),
    "badge": "hello_app.admin_callbacks.get_draft_count",
    "badge_type": BadgeType.WARNING,   # INFO, SUCCESS, WARNING, DANGER
}
```

### Tabs — вкладки для навігації між моделями

```
Changelist tabs:                    Changeform tabs:
┌──────────┬────────────┐          ┌──────────┬──────────┬──────────┐
│ Нотатки  │ Коментарі  │          │ Основне  │ SEO      │ Медіа    │
└──────────┴────────────┘          └──────────┴──────────┴──────────┘
[список нотаток]                   [форма редагування з вкладками]
```

```python
# settings.py — статичні tabs
"TABS": [
    {
        "models": ["hello_app.note", "hello_app.comment", "hello_app.category"],
        "items": [
            {
                "title": "Нотатки",
                "icon": "description",
                "link": reverse_lazy("admin:hello_app_note_changelist"),
            },
            {
                "title": "Коментарі",
                "icon": "comment",
                "link": reverse_lazy("admin:hello_app_comment_changelist"),
            },
            {
                "title": "Категорії",
                "icon": "label",
                "link": reverse_lazy("admin:hello_app_category_changelist"),
            },
        ],
    },
],
```

### Динамічні вкладки (callback)

```python
# hello_app/admin_callbacks.py

def note_tabs_callback(request):
    """Динамічні вкладки залежно від прав користувача."""
    tabs = [
        {
            "title": "Мої нотатки",
            "icon": "person",
            "link": f"{reverse('admin:hello_app_note_changelist')}?author={request.user.pk}",
        },
    ]
    if request.user.is_superuser:
        tabs.append({
            "title": "Всі нотатки",
            "icon": "groups",
            "link": reverse("admin:hello_app_note_changelist"),
        })
    return tabs
```

```python
# settings.py
"TABS": [
    {
        "models": ["hello_app.note"],
        "items": "hello_app.admin_callbacks.note_tabs_callback",
    },
],
```

---

---
- **🧠 Ментальна модель:** Django Admin Dashboard — це "порожній холст". Стандартна адмінка показує простий список додатків/моделей. `DASHBOARD_CALLBACK` — це твій "художник": він отримує порожній контекст і малює на ньому статистику, графіки, картки. Потім Unfold "вішає" цю картину у шаблоні `admin/index.html`.
- **📚 Чому callback замість context processor:** Context processor виконується для КОЖНОГО запиту до всієї адмінки. Dashboard дані потрібні тільки на головній сторінці. `DASHBOARD_CALLBACK` викликається тільки при відкритті `/admin/` — економія ресурсів. Також це явна ін'єкція даних: ти точно знаєш що і коли виконується.
- **🌐 Що відбувається під капотом:** При запиті до `/admin/` Unfold викликає функцію з `DASHBOARD_CALLBACK`. Ця функція отримує `(request, context)` — де `context` вже містить стандартні Django admin дані. Твоя функція МУТУЄ `context` словник (`context['stats'] = {...}`) і повертає його. Потім Unfold рендерить `admin/index.html` з цим збагаченим контекстом. Шаблон `index.html` у `templates/admin/` замінює стандартний.
- **❌ Типова помилка початківця:** Забути кешування в `DASHBOARD_CALLBACK`. Якщо функція виконує 5 складних SQL-запитів, вона буде їх виконувати при КОЖНОМУ завантаженні дашборду (кожен раз коли хтось відкриває `/admin/`). Завжди використовуй `cache.get/set` для агрегованих статистик із TTL 60-300 секунд.
---

## §9. Dashboard — layouts і DASHBOARD_CALLBACK

### Кастомний index.html

```python
# settings.py — вказуємо callback
"DASHBOARD_CALLBACK": "hello_app.admin_dashboard.dashboard_callback",
```

```python
# hello_app/admin_dashboard.py

from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import Note


def dashboard_callback(request, context):
    """
    Ін'єкція даних у шаблон admin/index.html.
    Виконується при кожному завантаженні дашборду.
    """
    # Статистика
    context['stats'] = {
        'total_notes': Note.objects.count(),
        'published': Note.objects.filter(status='published').count(),
        'drafts': Note.objects.filter(status='draft').count(),
        'today': Note.objects.filter(
            created_at__date=timezone.now().date()
        ).count(),
    }

    # Дані для графіка (останні 14 днів)
    two_weeks_ago = timezone.now() - timedelta(days=14)
    daily_counts = (
        Note.objects
        .filter(created_at__gte=two_weeks_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    context['chart_data'] = {
        'labels': [str(row['date']) for row in daily_counts],
        'datasets': [{
            'label': 'Нових нотаток',
            'data': [row['count'] for row in daily_counts],
        }],
    }

    return context
```

### Шаблон дашборду

```html
{# templates/admin/index.html #}
{% extends "unfold/layouts/base_simple.html" %}
{% load i18n unfold %}

{% block content %}
<div class="flex flex-col gap-6">

    {# ── Stats Cards ──────────────────────────── #}
    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {% component "unfold/components/card.html" with
            title="Всього нотаток"
            value=stats.total_notes
            icon="description"
            footer="За весь час"
        %}{% endcomponent %}

        {% component "unfold/components/card.html" with
            title="Опубліковано"
            value=stats.published
            icon="check_circle"
            class="bg-green-50"
        %}{% endcomponent %}

        {% component "unfold/components/card.html" with
            title="Чернетки"
            value=stats.drafts
            icon="edit_note"
            class="bg-yellow-50"
        %}{% endcomponent %}

        {% component "unfold/components/card.html" with
            title="Сьогодні"
            value=stats.today
            icon="today"
        %}{% endcomponent %}
    </div>

    {# ── Chart ────────────────────────────────── #}
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {% component "unfold/components/chart/line.html" with
            title="Нові нотатки (14 днів)"
            data=chart_data
        %}{% endcomponent %}

        {# Tracker — активність #}
        {% component "unfold/components/tracker.html" with
            title="Активність за рік"
            data=tracker_data
        %}{% endcomponent %}
    </div>

</div>
{% endblock %}
```

---

---
- **🧠 Ментальна модель:** Unfold Widgets — це "набір меблів преміум-класу" для дашборду. Card — це вітрина (одне число + контекст). Chart — це графік (Chart.js під капотом). Tracker — це теплова карта GitHub-активності. Cohort — це таблиця утримання (retention analysis). Кожен виджет — це Unfold компонент, що приймає Python-dict і рендерить відповідний HTML+JS.
- **📚 Чому компоненти замість прямого HTML:** Unfold `{% component %}` тег гарантує консистентний стиль (темна тема, кольори, відступи) без дублювання CSS. Ти передаєш дані через `with key=value`, компонент сам знає як їх відобразити. При оновленні Unfold — стиль компонентів оновлюється автоматично.
- **🌐 Що відбувається під капотом:** `{% component "unfold/components/chart/line.html" with data=chart_data %}` — це Django template tag `{% include %}` з додатковою логікою. Unfold рендерить частковий шаблон і ін'єктує в нього Python-словник `chart_data`. Шаблон Chart генерує `<canvas>` тег і `<script>` з `new Chart(ctx, {{ data|json_script }})`. Chart.js (JavaScript бібліотека) підхоплює `<canvas>` і малює графік у браузері.
- **❌ Типова помилка початківця:** Передавати в `data` Chart компонента Python QuerySet напряму. Unfold очікує Python dict з ключами `labels` і `datasets`. QuerySet потрібно попередньо перетворити в словник у `dashboard_callback`. Якщо цього не зробити — шаблон кине `TypeError` або відобразить порожній графік.
---

## §10. Widget Systems

### Card — базовий контейнер

```python
# context для card
{
    "title": "Нові реєстрації",
    "metric": "1,284",
    "footer": "+12% цього тижня",
    "icon": "person_add",
    "label": "Зростання",
    "label_value": "+12%",
}
```

```html
{% component "unfold/components/card.html" with
    title="Нові реєстрації"
    metric="1,284"
    icon="person_add"
    footer="+12% цього тижня"
%}{% endcomponent %}
```

### Chart — Chart.js інтеграція

```python
# Лінійний графік
chart_data = {
    "labels": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"],
    "datasets": [
        {
            "label": "Нотатки",
            "data": [12, 19, 8, 15, 22, 7, 11],
            "borderColor": "rgb(14, 165, 233)",
            "backgroundColor": "rgba(14, 165, 233, 0.1)",
            "fill": True,
        },
        {
            "label": "Коментарі",
            "data": [5, 8, 3, 7, 10, 2, 6],
            "borderColor": "rgb(168, 85, 247)",
        },
    ],
}
```

```html
{# Line chart #}
{% component "unfold/components/chart/line.html" with
    title="Активність за тиждень"
    data=chart_data
    height=300
%}{% endcomponent %}

{# Bar chart #}
{% component "unfold/components/chart/bar.html" with
    title="Нотатки по категоріях"
    data=bar_chart_data
%}{% endcomponent %}
```

### Tracker — теплова карта активності

```python
# Генерація даних для Tracker (схоже на GitHub contributions)
from datetime import date, timedelta
import random

def get_tracker_data():
    today = date.today()
    data = []
    for i in range(365):
        day = today - timedelta(days=i)
        count = Note.objects.filter(created_at__date=day).count()
        data.append({
            "date": str(day),
            "level": min(count, 4),  # 0-4 рівні інтенсивності
            "tooltip": f"{count} нотаток {day.strftime('%d.%m.%Y')}",
        })
    return list(reversed(data))
```

```html
{% component "unfold/components/tracker.html" with
    title="Активність за рік"
    data=tracker_data
%}{% endcomponent %}
```

### Cohort — таблиця утримання

```python
# Когортний аналіз — наприклад, утримання користувачів
cohort_data = {
    "columns": ["Тиждень 1", "Тиждень 2", "Тиждень 3", "Тиждень 4"],
    "rows": [
        {"label": "Лютий 2025", "values": [100, 72, 58, 45]},
        {"label": "Березень 2025", "values": [100, 68, 51, None]},
        {"label": "Квітень 2025", "values": [100, 71, None, None]},
    ],
}
```

```html
{% component "unfold/components/cohort.html" with
    title="Утримання користувачів"
    data=cohort_data
%}{% endcomponent %}
```

---

---
- **🧠 Ментальна модель:** Information Hierarchy — це архітектура уваги. Коли форма редагування має 20+ полів — користувач губиться. Fieldset Tabs розбивають поля на логічні групи (вкладки), показуючи тільки одну групу за раз. Conditional Fields ховають поля, що не стосуються поточного стану (наприклад, `visible_until` показується тільки якщо status='scheduled'). Sortable Inlines дозволяють перетягувати рядки мишею — без додаткового JavaScript коду.
- **📚 Чому Alpine.js для conditional fields:** Alpine.js — це "мінімалістичний React" (14KB), вбудований в Unfold. Він дозволяє реактивно показувати/ховати DOM-елементи через `x-show="condition"` без написання власного JavaScript. `x-data` визначає reactive state, `x-on:change` оновлює state при події. Браузер обробляє показ/приховування миттєво без запиту на сервер.
- **🌐 Що відбувається під капотом:** Fieldset Tabs в Unfold реалізовані через `'tab': True` у fieldsets. Unfold рендерить вкладки як `<nav>` з JavaScript перемикачем. При кліку на вкладку — Alpine.js показує відповідний fieldset і ховає інші. Дані всіх вкладок надсилаються разом при POST-збереженні (не тільки активної вкладки). Sortable Inlines використовують SortableJS (JavaScript) для drag-and-drop, зберігаючи порядок у hidden input.
- **❌ Типова помилка початківця:** Додавати `'tab': True` не до всіх fieldsets — деякі fields опиняться поза вкладками і будуть відображатися внизу сторінки в "сирому" вигляді. Або забути встановити `from unfold.admin import ModelAdmin as UnfoldModelAdmin` — fieldset tabs не будуть рендеруватися стандартним `ModelAdmin`.
---

## §11. Information Hierarchy

### Fieldset Tabs — вкладки у формі

```python
from unfold.admin import ModelAdmin as UnfoldModelAdmin

@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    fieldsets = [
        (
            'Основна інформація',
            {
                'tab': True,        # ← перша вкладка
                'fields': ['title', 'body', 'category'],
            }
        ),
        (
            'SEO',
            {
                'tab': True,        # ← друга вкладка
                'fields': ['slug', 'meta_title', 'meta_description'],
            }
        ),
        (
            'Публікація',
            {
                'tab': True,        # ← третя вкладка
                'fields': ['status', 'published_at', 'is_public'],
            }
        ),
    ]
```

### Conditional Fields — Alpine.js

```python
# Поле visible_until показується тільки якщо status == 'scheduled'

@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    fieldsets = [
        (
            None,
            {
                'fields': [
                    'title',
                    'status',
                    'visible_until',   # умовне поле
                ],
            }
        ),
    ]
```

```html
{# templates/admin/hello_app/note/change_form.html #}
{% extends "admin/change_form.html" %}

{% block field_sets %}
<div x-data="{ status: '{{ adminform.form.initial.status }}' }">

    {# status field — при зміні оновлює x-data #}
    <div x-on:change="status = $event.target.value">
        {{ block.super }}
    </div>

    {# visible_until — показується тільки для scheduled #}
    <div x-show="status === 'scheduled'" x-cloak>
        {# поле форми #}
    </div>
</div>
{% endblock %}
```

### Sortable Inlines

```python
from unfold.contrib.inlines.admin import SortableStackedInline

class SortableAttachmentInline(SortableStackedInline):
    model = Attachment
    fields = ['file', 'description', 'order']
    sortable_field_name = 'order'   # поле для сортування (IntegerField)
    extra = 0
```

### Expandable Rows у ChangeList

```python
from unfold.admin import ModelAdmin as UnfoldModelAdmin

@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    list_display = ['title', 'status', 'comments_count']
    # Expandable row — розгорнутий рядок з preview
    list_expandable_fields = True

    def get_expandable_data(self, obj):
        """Дані для розгорнутого рядка."""
        return {
            'preview': obj.body[:200] + '...' if len(obj.body) > 200 else obj.body,
            'comments': obj.comments.values_list('text', flat=True)[:3],
        }
```

---

---
- **🧠 Ментальна модель:** Enterprise Patterns — це "поповерховий офіс". Різні команди (операційна, аналітична, технічна підтримка) потребують різних "поверхів" з різним видом і доступом. `UnfoldAdminSite` + `LegacyAdminSite` дозволяють мати кілька адмін-панелей на одному Django-сервері: сучасна Unfold для нових фіч, стандартна для legacy workflows. `InfinitePaginator` — для таблиць з мільйонами рядків де `COUNT(*)` займає секунди.
- **📚 Чому `InfinitePaginator` важливий:** PostgreSQL `COUNT(*)` на таблиці з 10M рядків без умов може займати 2-5 секунд (full table scan або index scan). Стандартна Django пагінація виконує `COUNT(*)` при КОЖНОМУ завантаженні списку. `InfinitePaginator` використовує `LIMIT N+1` замість COUNT: якщо отримали N+1 рядків — є ще одна сторінка; якщо менше N+1 — це остання. Без підрахунку загальної кількості.
- **🌐 Що відбувається під капотом:** `import/export + Unfold` — Unfold замінює стандартні шаблони `django-import-export` своїми Tailwind-стилізованими версіями. `unfold.contrib.import_export` містить overridden шаблони для Import/Export кнопок і модальних вікон. Django знаходить їх першими (бо `unfold` першим у `INSTALLED_APPS`).
- **❌ Типова помилка початківця:** Встановити `unfold.contrib.import_export` але залишити `'import_export'` перед `'unfold'` в `INSTALLED_APPS`. Результат: стандартні (не Tailwind) шаблони import_export завантажуються першими — кнопки виглядають інакше всієї адмінки.
---

## §12. Enterprise Patterns

### Паралельний Unfold + стандартний admin

```python
# hello_app/admin_sites.py

from unfold.sites import UnfoldAdminSite
from django.contrib.admin import AdminSite

# Unfold для нової команди
class ModernAdminSite(UnfoldAdminSite):
    site_header = 'Bootstrap Notes Modern'

# Стандартний для legacy workflows
class LegacyAdminSite(AdminSite):
    site_header = 'Bootstrap Notes Legacy'

modern_admin = ModernAdminSite(name='modern')
legacy_admin = LegacyAdminSite(name='legacy')
```

```python
# urls.py
urlpatterns = [
    path('admin/', admin.site.urls),            # стандартний Django Admin
    path('modern/', modern_admin.urls),         # Unfold
    path('legacy/', legacy_admin.urls),         # legacy AdminSite
]
```

### InfinitePaginator — без COUNT(*)

```python
from unfold.paginator import InfinitePaginator

@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    paginator = InfinitePaginator    # ← без COUNT(*) запиту
    list_per_page = 50
    show_full_result_count = False   # сховати "X results (Y total)"
```

> **Навіщо:** `SELECT COUNT(*) FROM notes` на таблиці з 10M рядків може займати секунди.
> `InfinitePaginator` використовує `LIMIT/OFFSET` без підрахунку загальної кількості.

### crispy-forms + Unfold

```bash
pip install crispy-tailwind
```

```python
# settings.py
INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.forms',    # ← Unfold форми
    'crispy_forms',
    'crispy_tailwind',
    ...
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"
```

```python
# forms.py — crispy з Unfold стилями
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class NoteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            Row(Column('category'), Column('status')),
            'body',
            Submit('submit', 'Зберегти', css_class='btn-primary'),
        )
```

### import/export + Unfold

```bash
pip install django-import-export
```

```python
# settings.py
INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.import_export',  # ← замість 'import_export'
    'import_export',
    ...
]
```

```python
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from import_export import resources


class NoteResource(resources.ModelResource):
    class Meta:
        model = Note
        fields = ['id', 'title', 'body', 'status', 'created_at']


@admin.register(Note)
class NoteAdmin(ImportExportModelAdmin, UnfoldModelAdmin):
    resource_classes = [NoteResource]
    # → з'являються кнопки Import/Export у ChangeList
```

### Command Palette (Ctrl+K)

```python
# settings.py — глобальний пошук
UNFOLD = {
    ...
    "COMMAND_PALETTE": {
        "show_search": True,
        # search_fields беруться з ModelAdmin.search_fields
        # Увага: може бути навантаженням на БД!
        # Конфігуруйте search_fields з ^ або = префіксами
    },
}
```

> **Production попередження:** Command palette виконує пошук по всіх зареєстрованих моделях одночасно. Перевірте що в кожного `ModelAdmin` є `search_fields` з індексованими полями.

---

---
- **🧠 Ментальна модель:** Anti-Patterns — це "добре виглядає зараз, болить потім". Кожен з перерахованих анти-патернів має короткострокову перевагу ("менше коду зараз") і довгострокову ціну ("XSS вразливість", "падіння під навантаженням", "баг у concurrency"). Вивчення анти-патернів рятує від технічного боргу.
- **📚 Чому `format_html` а не `mark_safe`:** `mark_safe(f'<b>{obj.title}</b>')` — Python f-string інтерполює `obj.title` напряму. Якщо title = `'<script>alert("xss")</script>'` — шаблон рендерить реальний `<script>` тег. XSS-атака. `format_html('<b>{}</b>', obj.title)` автоматично екранує другий аргумент: `<script>` → `&lt;script&gt;`. Безпечно, навіть якщо title є user-generated content.
- **🌐 Що відбувається під капотом:** Django `format_html` всередині викликає `conditional_escape()` для кожного аргументу, який не є `SafeData`. Це перетворює `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`, `'` → `&#x27;`, `&` → `&amp;`. Результат — рядок позначений як `SafeData`, який Django Template не буде екранувати повторно.
- **❌ Типова помилка початківця:** Думати "у мене адмінка закрита паролем — XSS не проблема". XSS в адмінці особливо небезпечний: якщо зловмисник може ввести JavaScript у title нотатки, і staff-користувач відкриє список нотаток в адмінці — JS виконається в контексті session staff-користувача з повними правами.
---

## §13. Admin Anti-Patterns

### ❌ Адмінка як основний frontend

```python
# НЕПРАВИЛЬНО: бізнес-процеси зовнішніх користувачів в адмінці
# Адмінка для ВНУТРІШНЬОГО персоналу
# Зовнішні користувачі → стандартні Django Views + Bootstrap templates
```

### ❌ State Leakage через мутацію атрибутів

```python
# ❌ НЕБЕЗПЕЧНО: ModelAdmin є синглтоном!
class NoteAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            self.readonly_fields.append('title')  # мутує клас для ВСІХ
        return self.readonly_fields

# ✅ Повертати новий список
    def get_readonly_fields(self, request, obj=None):
        fields = list(self.readonly_fields)  # копія
        if obj:
            fields.append('title')
        return fields
```

### ❌ XSS через mark_safe

```python
# ❌ НЕБЕЗПЕЧНО: user-generated content без escape
def colored_title(self, obj):
    return mark_safe(f'<b>{obj.title}</b>')  # title може містити <script>!

# ✅ format_html екранує автоматично
from django.utils.html import format_html

def colored_title(self, obj):
    return format_html('<b>{}</b>', obj.title)  # безпечно
```

### ❌ Повільний search_fields без індексів

```python
# ❌ Full scan на TEXT полі
search_fields = ['body']  # WHERE body LIKE '%query%' — no index!

# ✅ Пошук по індексованих полях
search_fields = ['^title']   # startswith — використовує btree index
# Або додати GIN індекс для full-text search у PostgreSQL:
# CREATE INDEX idx_note_body_gin ON notes_note USING gin(to_tsvector('ukrainian', body));
```

### ❌ Кастомні URL без admin_view

```python
# ❌ Незахищений endpoint
def get_urls(self):
    return [
        path('export/', self.export_view),  # ВІДКРИТИЙ ДЛЯ ВСІХ!
    ] + super().get_urls()

# ✅ Обгортка admin_view гарантує автентифікацію
def get_urls(self):
    return [
        path('export/',
             self.admin_site.admin_view(self.export_view)),  # захищено
    ] + super().get_urls()
```

### ❌ N+1 у list_display без list_select_related

```python
# ❌ 1 + N запитів (N = кількість нотаток на сторінці)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_email']

    def author_email(self, obj):
        return obj.author.email  # SELECT для кожного рядка

# ✅
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_email']
    list_select_related = ['author']  # JOIN один раз

    def author_email(self, obj):
        return obj.author.email  # з кешу
```

---

## §14. Питання для самоперевірки

1. `AdminSite` є синглтоном. Що це означає для методу `get_readonly_fields()`? Чому мутація `self.readonly_fields` небезпечна?
2. Для чого потрібен `self.admin_site.admin_view()` при додаванні кастомного URL у `get_urls()`? Що станеться без нього?
3. `list_select_related = True` vs `list_select_related = ['author', 'category']` — яка різниця?
4. `search_fields = ['body']` на таблиці з 1M рядків. Що відбувається в БД? Як виправити?
5. `TemplateResponse` у `changelist_view` дозволяє middleware змінити контекст. Як це використати для A/B тестування?
6. Unfold `InfinitePaginator` не виконує `COUNT(*)`. Які обмеження це накладає на UX? Коли це прийнятно?
7. Чому Command Palette може бути небезпечним у production без правильної конфігурації `search_fields`?
8. `DASHBOARD_CALLBACK` отримує `(request, context)` — чим це відрізняється від стандартного Context Processor?
9. `SortableStackedInline` вимагає `IntegerField` у моделі. Чому? Як це поле зберігається в БД?
10. Можна запустити одночасно стандартний `django.contrib.admin.site` і `UnfoldAdminSite` на різних URL? Яка практична перевага цього в enterprise?

---

---
- **🧠 Ментальна модель:** Unfold Filters — це "розумний пошук" замість "тупого dropdown". Стандартний `list_filter = ['author']` для FK з 100k користувачів завантажує ВСІХ у `<select>` — сторінка підвисає. `AutocompleteSelectFilter` завантажує тільки 10 результатів через AJAX при введенні. `RangeDateFilter` показує "від/до" поля замість списку років. `TextFilter` — текстове поле з кастомною логікою.
- **📚 Чому `list_filter_submit = True` обов'язковий для деяких фільтрів:** Без `list_filter_submit` кожна зміна фільтра миттєво відправляє запит на сервер (стандартна поведінка). Для `RangeDateFilter` та `TextFilter` — поля вводу, це означало б запит після кожного натиснутого символу. `list_filter_submit = True` додає кнопку "Застосувати" і відправляє запит тільки після явного підтвердження.
- **🌐 Що відбувається під капотом:** `AutocompleteSelectFilter` під капотом використовує Django вбудований autocomplete API: `GET /admin/auth/user/autocomplete/?term=john&app_label=hello_app&model_name=note&field_name=author`. Django Admin виконує `search_fields` query на UserAdmin і повертає JSON з результатами. Тому `search_fields` на `UserAdmin` є ОБОВ'ЯЗКОВИМ для роботи `AutocompleteSelectFilter`.
- **❌ Типова помилка початківця:** Підключити `AutocompleteSelectFilter` для `author` FK, але не додати `search_fields` на `UserAdmin`. Django поверне `Http404` або `ImproperlyConfigured` при AJAX-запиті autocomplete. Правило: якщо FK вказує на модель X — у `XAdmin` ПОВИНЕН бути `search_fields`.
---

## §15. Advanced Filtering — Unfold Filters

### Вбудовані фільтри Unfold

```python
# settings.py
INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',   # ← обов'язково
    ...
]
```

```python
# hello_app/admin.py
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,       # Select2 пошук для FK
    AutocompleteSelectMultipleFilter,
    RangeDateFilter,                # вибір діапазону дат
    RangeDateTimeFilter,
    RangeNumericFilter,             # числовий діапазон
    TextFilter,                     # текстовий фільтр з полем вводу
    DropdownFilter,                 # стандартний dropdown
    RelatedDropdownFilter,          # FK dropdown
    ChoicesDropdownFilter,          # choices field dropdown
)

@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    list_filter_submit = True       # ← кнопка "Застосувати" у фільтрах

    list_filter = [
        ('status', ChoicesDropdownFilter),          # dropdown для choices
        ('category', RelatedDropdownFilter),        # FK dropdown
        ('author', AutocompleteSelectFilter),       # Select2 AJAX
        ('created_at', RangeDateFilter),            # від/до для дати
    ]
```

### TextFilter — кастомний текстовий фільтр

```python
from unfold.contrib.filters.admin import TextFilter

class TitleTextFilter(TextFilter):
    title = 'Пошук по заголовку'
    parameter_name = 'title_contains'

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(title__icontains=self.value())
        return queryset


@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    list_filter = [TitleTextFilter]
```

### AutocompleteSelectFilter для великих FK

```python
# ❌ Стандартний list_filter для FK з 100k записів
list_filter = ['author']
# → SELECT * FROM auth_user → завантажує ВСІ записи у <select>

# ✅ AutocompleteSelectFilter — AJAX пошук
from unfold.contrib.filters.admin import AutocompleteSelectFilter

list_filter = [('author', AutocompleteSelectFilter)]
list_filter_submit = True

# Потрібно щоб UserAdmin мав search_fields
@admin.register(User)
class UserAdmin(UserAdmin):
    search_fields = ['^username', '^email']  # ← обов'язково
```

### RangeDateTimeFilter — діапазон дат

```python
from unfold.contrib.filters.admin import RangeDateTimeFilter

@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    list_filter = [
        ('created_at', RangeDateTimeFilter),  # → "Від: [дата] До: [дата]"
    ]
    list_filter_submit = True  # без submit — фільтр не спрацьовує!
```

---

---
- **🧠 Ментальна модель:** Actions — це "масові операції". Стандартний Django "select all + delete" — це теж action. Unfold розширює систему actions трьома рівнями: (1) Bulk actions (для вибраних записів у списку), (2) Dialog actions (bulk дія з формою підтвердження), (3) Row-level actions (для кожного рядка окремо). Dialog action — це "два кроки замість одного": спочатку форма (причина, параметри), потім дія.
- **📚 Чому Dialog Actions замість простого підтвердження:** Browser `confirm()` — це блокуюче модальне вікно без можливості введення даних. `BaseDialogForm` — це повноцінна Django форма в модальному вікні: поля введення, валідація, Bootstrap стилі. Наприклад, при архівуванні нотатки — запитати причину і чи повідомляти автора. Ці дані передаються у `request.POST` і доступні в action методі.
- **🌐 Що відбувається під капотом:** Bulk action flow: (1) Користувач вибирає checkbox-и в ChangeList, (2) Вибирає action з dropdown, (3) POST запит на `/admin/hello_app/note/` з `action='publish_notes'` і `_selected_action=[1, 2, 3]`, (4) Django знаходить метод `publish_notes` в `NoteAdmin.actions`, (5) Викликає `publish_notes(modeladmin, request, queryset)` де `queryset` вже відфільтрований по вибраних записах.
- **❌ Типова помилка початківця:** Виконувати дорогу операцію (наприклад, відправку email) у bulk action синхронно. Якщо обрати 1000 записів і натиснути "Архівувати і повідомити" — HTTP запит займе хвилини. Браузер може втратити з'єднання. Важкі операції у bulk actions — завжди через Celery task.
---

## §16. Bulk Actions і Dialog Actions

### Стандартні actions + Unfold декоратор

```python
from unfold.decorators import action

@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    actions = ['publish_notes', 'delete_with_confirm']

    @action(
        description='Опублікувати',
        icon='publish',
        attrs={'class': 'text-green-600 font-semibold'},
    )
    def publish_notes(self, request, queryset):
        count = queryset.update(status='published')
        self.message_user(request, f'Опубліковано {count} нотаток.')
```

### Dialog Action — підтвердження з формою

```python
from unfold.actions import BaseDialogForm, BaseActionForm
from django import forms

class ArchiveReasonForm(BaseDialogForm):
    """Форма для діалогового вікна перед архівуванням."""
    reason = forms.CharField(
        label='Причина архівування',
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True,
    )
    notify_author = forms.BooleanField(
        label='Повідомити автора',
        required=False,
        initial=True,
    )


@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    actions = ['archive_with_reason']

    @action(
        description='Архівувати з поясненням',
        icon='archive',
        form=ArchiveReasonForm,                 # ← відкриває модальне вікно
    )
    def archive_with_reason(self, request, queryset):
        # Після заповнення форми — тут є request.POST
        reason = request.POST.get('reason', '')
        notify = request.POST.get('notify_author') == 'on'

        for note in queryset:
            note.status = 'archived'
            note.archive_reason = reason
            note.save()
            if notify:
                send_mail(
                    subject='Ваша нотатка архівована',
                    message=f'Причина: {reason}',
                    recipient_list=[note.author.email],
                    from_email=settings.DEFAULT_FROM_EMAIL,
                )

        self.message_user(request, f'Архівовано {queryset.count()} нотаток.')
```

### Row-level actions (дії на кожному рядку)

```python
from unfold.admin import ModelAdmin as UnfoldModelAdmin

@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):

    @action(description='Дублювати', icon='content_copy', url_path='duplicate')
    def duplicate_note(self, request, pk):
        """Row-level action — для кожного рядка окремо."""
        note = get_object_or_404(Note, pk=pk)
        note.pk = None
        note.title = f'[Копія] {note.title}'
        note.status = 'draft'
        note.save()
        self.message_user(request, f'Нотатку продубльовано.')
        return redirect(
            reverse('admin:hello_app_note_changelist')
        )
```

---

---
- **🧠 Ментальна модель:** Component Classes — це "окремий відділ" для кожного дашборд-блоку. Замість одного великого `dashboard_callback` що робить все — кожен компонент (графік активності, таблиця топ-авторів, трекер) є окремим класом з власним `get_context_data()`. Це "розділення відповідальності" у чистому вигляді: тестується окремо, оновлюється окремо, кешується окремо.
- **📚 Чому `apps.py → ready()` для реєстрації:** `@register_component` реєструє компонент у глобальний реєстр при імпорті модуля. Але Python не імпортує модуль автоматично — лише якщо він явно import-ований. `apps.py → ready()` — це правильне місце для "побічних ефектів при старті Django": він виконується після повного завантаження всіх моделей і налаштувань. `import hello_app.admin_components` у `ready()` ініціює реєстрацію.
- **🌐 Що відбувається під капотом:** `{% component "hello_app.admin_components.NoteActivityChartComponent" %}` — Unfold знаходить клас у реєстрі за рядковим шляхом, створює екземпляр, викликає `get_context_data()`, і рендерить вміст блоку компонента у цьому контексті. Вміст між `{% component %}` і `{% endcomponent %}` — це шаблон компонента, якому доступні дані з `get_context_data()`.
- **❌ Типова помилка початківця:** Забути `import hello_app.admin_components` у `apps.py → ready()`. Компоненти не будуть зареєстровані. `{% component "..." %}` тихо відобразить нічого або кине `ComponentNotFound`. Перевірка: після зупинки та перезапуску сервера — помилка `ComponentNotFound` → `ready()` не імпортує потрібний модуль.
---

## §17. Component Classes — `@register_component`

### Навіщо Component Classes

```
❌ Dashboard callback із важкою логікою:
def dashboard_callback(request, context):
    context['chart'] = {
        'labels': [...heavy ORM aggregation...],
        'data': [...more complex stuff...],
    }
    # Все змішане в одній функції

✅ Component Class — логіка ізольована:
@register_component
class NoteActivityChart:
    def get_context_data(self, **kwargs):
        return {'labels': [...], 'data': [...]}
```

### Реєстрація і використання

```python
# hello_app/admin_components.py

from unfold.components import BaseComponent, register_component
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.utils import timezone


@register_component
class NoteActivityChartComponent(BaseComponent):
    """Лінійний графік активності за 30 днів."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily = (
            Note.objects
            .filter(created_at__gte=thirty_days_ago)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        context['chart_data'] = {
            'labels': [str(row['date']) for row in daily],
            'datasets': [{
                'label': 'Нових нотаток',
                'data': [row['count'] for row in daily],
                'borderColor': 'rgb(14, 165, 233)',
                'backgroundColor': 'rgba(14, 165, 233, 0.1)',
                'fill': True,
            }],
        }
        context['title'] = 'Активність за 30 днів'
        return context


@register_component
class TopAuthorsTableComponent(BaseComponent):
    """Топ-5 авторів по кількості нотаток."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        top_authors = (
            Note.objects
            .values('author__username')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        context['authors'] = top_authors
        return context
```

```python
# hello_app/apps.py — щоб компоненти завантажились
class HelloAppConfig(AppConfig):
    name = 'hello_app'

    def ready(self):
        import hello_app.admin_components  # ← реєстрація компонентів
```

```html
{# templates/admin/index.html #}
{% extends "unfold/layouts/base_simple.html" %}
{% load unfold %}

{% block content %}
<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">

    {# Component Class — автоматично викликає get_context_data() #}
    {% component "hello_app.admin_components.NoteActivityChartComponent" %}
    {% component "hello_app/components/chart/line.html" with data=chart_data title=title %}
    {% endcomponent %}
    {% endcomponent %}

    {% component "hello_app.admin_components.TopAuthorsTableComponent" %}
    <table class="w-full text-sm">
        {% for author in authors %}
        <tr>
            <td>{{ author.author__username }}</td>
            <td class="text-right font-bold">{{ author.count }}</td>
        </tr>
        {% endfor %}
    </table>
    {% endcomponent %}

</div>
{% endblock %}
```

---

---
- **🧠 Ментальна модель:** Custom Pages — це "власний кабінет в офісі". Стандартна адмінка знає тільки CRUD (список, форма, видалення). Якщо потрібна аналітична сторінка, звіт, або кастомна форма без прив'язки до моделі — `UnfoldModelAdminViewMixin + TemplateView`. Це Django Class-Based View всередині адмінки, зі стилями Unfold, sidebar, breadcrumbs і перевіркою прав — але з власним шаблоном і логікою.
- **📚 Чому `admin_view()` обов'язковий:** `self.admin_site.admin_view(view)` — це decorator, який обгортає view і додає: (1) перевірку автентифікації (redirect на login якщо не авторизований), (2) перевірку `is_staff` (403 якщо не staff), (3) CSRF перевірку. Без нього — твоя кастомна сторінка відкрита для всіх без авторизації. Це критична вразливість безпеки.
- **🌐 Що відбувається під капотом:** `NoteStatisticsView.as_view(model_admin=self)` — `model_admin` передається у view через `kwargs`. `UnfoldModelAdminViewMixin` використовує `model_admin` для доступу до `admin_site.each_context()` (глобальні admin контекст змінні: права, повідомлення, sidebar дані). Без `model_admin` — Unfold шаблон не зможе побудувати sidebar і navbar.
- **❌ Типова помилка початківця:** Реєструвати кастомну сторінку в `get_urls()` але забути додати посилання у `UNFOLD.SIDEBAR`. Сторінка технічно доступна (якщо знаєш URL), але недосяжна через інтерфейс. Або реєструвати URL без `name=` — тоді `reverse_lazy('admin:...')` у sidebar кине `NoReverseMatch`.
---

## §18. Custom Pages — UnfoldModelAdminViewMixin

### Кастомна сторінка всередині Unfold

```python
# hello_app/admin_views.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from unfold.views import UnfoldModelAdminViewMixin


class NoteStatisticsView(UnfoldModelAdminViewMixin, TemplateView):
    """Власна сторінка статистики зі стилями Unfold."""
    title = 'Статистика нотаток'    # відображається в заголовку
    permission_required = ()         # або ('hello_app.view_note',)
    template_name = 'admin/hello_app/note_statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'by_status': Note.objects.values('status').annotate(
                count=Count('id')
            ),
            'by_month': Note.objects.annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(count=Count('id')).order_by('month'),
        }
        return context
```

```python
# hello_app/admin.py — реєстрація URL

@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):

    def get_urls(self):
        from django.urls import path
        from hello_app.admin_views import NoteStatisticsView

        urls = super().get_urls()
        custom = [
            path(
                'statistics/',
                self.admin_site.admin_view(           # ← захист автентифікацією
                    NoteStatisticsView.as_view(
                        model_admin=self              # ← передаємо ModelAdmin
                    )
                ),
                name='hello_app_note_statistics',
            ),
        ]
        return custom + urls
```

```python
# settings.py — додаємо сторінку до sidebar
UNFOLD = {
    "SIDEBAR": {
        "navigation": [
            {
                "title": "Аналітика",
                "items": [
                    {
                        "title": "Статистика нотаток",
                        "icon": "bar_chart",
                        "link": reverse_lazy("admin:hello_app_note_statistics"),
                    },
                ],
            },
        ],
    },
}
```

```html
{# templates/admin/hello_app/note_statistics.html #}
{% extends "unfold/layouts/base.html" %}
{% load i18n unfold %}

{% block breadcrumbs %}
<a href="{% url 'admin:hello_app_note_changelist' %}">Нотатки</a> /
<span>Статистика</span>
{% endblock %}

{% block content %}
<div class="flex flex-col gap-6">
    <h1 class="text-2xl font-bold">Статистика нотаток</h1>

    {# По статусах #}
    <div class="grid grid-cols-3 gap-4">
        {% for item in stats.by_status %}
        {% component "unfold/components/card.html" with
            title=item.status
            metric=item.count
        %}{% endcomponent %}
        {% endfor %}
    </div>
</div>
{% endblock %}
```

---

---
- **🧠 Ментальна модель:** Advanced Widgets — це "спеціальні інструменти для особливих полів". Стандартний `<textarea>` для тексту — це "молоток". `WysiwygWidget` — це "електродриль": WYSIWYG редактор з форматуванням (жирний, курсив, списки, посилання) прямо в адмінці. `ArrayWidget` — це "набір відміток": редагування PostgreSQL масиву як набору тегів-chips. `autocomplete_fields` — це "розумний пошук" замість "величезного select".
- **📚 Чому `formfield_for_dbfield` а не `widgets` у Meta:** `formfield_for_dbfield` дозволяє умовну логіку: різний widget залежно від назви поля, типу поля, або навіть request (наприклад, різний widget для superuser і звичайного staff). `widgets` у `ModelForm.Meta` — статична конфігурація без умов. Для кастомних Unfold widgets — завжди `formfield_for_dbfield`.
- **🌐 Що відбувається під капотом:** `WysiwygWidget` рендерить Trix (або TipTap) JavaScript редактор. При завантаженні форми — textarea перетворюється на rich-text редактор (JS ініціалізація). При збереженні — JS серіалізує відформатований вміст у HTML рядок і записує у приховане textarea. Django отримує HTML рядок у `request.POST` і зберігає його у `TextField`. При відображенні — `{{ note.body|safe }}` показує HTML.
- **❌ Типова помилка початківця:** Зберігати WYSIWYG HTML у `TextField` і відображати через `{{ note.body }}` (без `|safe`) у публічних шаблонах — текст відобразиться як `&lt;p&gt;...&lt;/p&gt;`. Або навпаки: `{{ user_comment|safe }}` для user-generated content без WYSIWYG — пряма XSS вразливість. Правило: `|safe` тільки для контенту, відредагованого через довірений WYSIWYG у закритій адмінці.
---

## §19. Advanced Widgets

### WysiwygWidget — WYSIWYG редактор (Trix)

```python
pip install django-trix  # або вбудований unfold Trix
```

```python
from unfold.contrib.forms.widgets import WysiwygWidget

@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'body':
            kwargs['widget'] = WysiwygWidget
        return super().formfield_for_dbfield(db_field, request, **kwargs)
```

### ArrayWidget — PostgreSQL Array поля

```python
# models.py — PostgreSQL ArrayField
from django.contrib.postgres.fields import ArrayField

class Note(models.Model):
    tags = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
    )
```

```python
from unfold.contrib.forms.widgets import ArrayWidget

@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'tags':
            kwargs['widget'] = ArrayWidget
        return super().formfield_for_dbfield(db_field, request, **kwargs)
        # → рендерить теги як chips з можливістю додавати/видаляти
```

### Autocomplete FK — заміна select

```python
@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    # ❌ Завантажує всіх users у <select>
    # raw_id_fields = ['author']

    # ✅ AJAX пошук — не завантажує всіх
    autocomplete_fields = ['author', 'category']

    # Потрібно на UserAdmin і CategoryAdmin:
    # search_fields = ['^username']  або  search_fields = ['^name']
```

---

---
- **🧠 Ментальна модель:** Admin Performance — це "фільтрація перед входом". Cache — це "вахтер з пам'яттю": перший раз він пускає тебе, перевіряє документи (виконує SQL), і записує результат. Наступний раз — просто відкриває двері без перевірки. `cache.set(key, value, timeout=300)` → 5 хвилин без SQL. `cache.delete(key)` при зміні даних → "вахтер забуває" → наступний запит знову перевіряє.
- **📚 Чому `cached.Loader` критичний у production:** Без `cached.Loader` Django читає файл шаблону з диску і парсить його при КОЖНОМУ запиті. 1000 запитів/секунда = 1000 читань диску + 1000 парсингів. `cached.Loader` парсить один раз при першому запиті і зберігає compiled Node tree в RAM. Наступні 999 запитів — тільки рендеринг з RAM. 10-50x прискорення рендерингу шаблонів.
- **🌐 Що відбувається під капотом:** PostgreSQL Full-Text Search з `SearchVector` і `GIN` індексом: `to_tsvector('ukrainian', title || ' ' || body)` — перетворює текст на lexemes (нормалізовані слова). `SearchQuery('django')` — теж нормалізується. GIN індекс зберігає `{lexeme → [doc_id, ...]}` mapping. Пошук — бінарний пошук по B-tree індексу GIN замість `LIKE '%query%'` full scan.
- **❌ Типова помилка початківця:** Увімкнути `cached.Loader` в development. При зміні шаблону — браузер показує стару версію. Потрібен перезапуск сервера щоб оновити кеш. `cached.Loader` — ВИКЛЮЧНО для production. В development залиш `APP_DIRS: True`.
---

## §20. Performance і Caching

### Кешування dashboard даних

```python
# hello_app/admin_dashboard.py

from django.core.cache import cache
from django.db.models import Count


def dashboard_callback(request, context):
    # Спроба отримати з кешу
    cache_key = 'admin_dashboard_stats'
    stats = cache.get(cache_key)

    if stats is None:
        # Важкий запит — виконується тільки якщо кеш порожній
        stats = {
            'total': Note.objects.count(),
            'published': Note.objects.filter(status='published').count(),
            'by_category': list(
                Note.objects.values('category__name')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            ),
        }
        cache.set(cache_key, stats, timeout=300)  # 5 хвилин

    context['stats'] = stats

    # Інвалідація кешу — в signal або save_model
    return context
```

```python
# Інвалідація при збереженні нотатки
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_save, sender=Note)
def invalidate_dashboard_cache(sender, **kwargs):
    cache.delete('admin_dashboard_stats')
```

### `{% cache %}` template tag для важких блоків

```html
{# templates/admin/index.html #}
{% load cache %}

{# Кешування HTML фрагменту на 5 хвилин #}
{% cache 300 "dashboard_top_authors" %}
    {% component "unfold/components/card.html" with
        title="Топ автори"
        data=top_authors
    %}{% endcomponent %}
{% endcache %}
```

### cached.Loader для шаблонів у production

```python
# settings.py — production
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': False,     # ← False коли використовуємо cached.Loader
        'OPTIONS': {
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
            'context_processors': [...],
        },
    },
]
```

### Full-text Search у PostgreSQL

```python
# ❌ LIKE на великій таблиці
search_fields = ['body']  # WHERE body LIKE '%query%' — full scan

# ✅ PostgreSQL Full-Text Search
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    search_fields = ['title']  # fallback для simple search

    def get_search_results(self, request, queryset, search_term):
        if search_term and len(search_term) >= 3:
            # Full-text search по title + body
            search_vector = SearchVector('title', weight='A') + \
                            SearchVector('body', weight='B')
            search_query = SearchQuery(search_term, config='ukrainian')

            queryset = (
                queryset
                .annotate(search=search_vector)
                .filter(search=search_query)
                .annotate(rank=SearchRank(search_vector, search_query))
                .order_by('-rank')
            )
            return queryset, False  # False = no distinct needed

        return super().get_search_results(request, queryset, search_term)
```

```sql
-- Міграція: GIN індекс для full-text search
-- hello_app/migrations/0002_note_search_index.py

from django.db import migrations

class Migration(migrations.Migration):
    operations = [
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_note_fts ON hello_app_note "
            "USING gin(to_tsvector('ukrainian', title || ' ' || body));",
            reverse_sql="DROP INDEX IF EXISTS idx_note_fts;",
        ),
    ]
```

### collectstatic для production

```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Hash-файли для агресивного browser caching
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
# → main.css → main.02b59bcc5cd9.css
# → Браузер кешує на рік (immutable)
# → Після зміни файлу hash змінюється → примусове оновлення
```

```bash
python manage.py collectstatic --noinput
# → збирає всі static files + admin/unfold assets
# → генерує staticfiles.json з маппінгом
```

---

---
- **🧠 Ментальна модель:** Datasets — це "таблиця всередині форми". Стандартний Inline показує 5-10 пов'язаних записів без пагінації. Якщо у нотатки 500 коментарів — Inline завантажить їх усі одразу (повільно, занадто). Dataset — це embedded ChangeList з пагінацією, фільтрами і пошуком. Це "міні-адмінка для пов'язаних записів" прямо у формі батьківського об'єкта.
- **📚 Чому partial view через URL замість Inline:** Inline виконує queryset синхронно при завантаженні форми. 500 коментарів = 1 важкий SQL + рендеринг 500 рядків. Dataset view виконується окремим HTTP-запитом (через `<iframe>` або HTMX), після завантаження основної форми. Форма завантажується швидко, коментарі догружаються асинхронно.
- **🌐 Що відбувається під капотом:** `comments_dataset_view` — це стандартний Django view, зареєстрований у `get_urls()`. Він виконується окремим HTTP-запитом (GET `/admin/hello_app/note/42/comments/?page=2`). `self.admin_site.each_context(request)` додає стандартні admin контекст змінні (права, sidebar, повідомлення), щоб partial шаблон виглядав як частина адмінки.
- **❌ Типова помилка початківця:** Забути `**self.admin_site.each_context(request)` у context dataset view. Шаблон Dataset не матиме доступу до `user`, `site_header`, sidebar navigation — він відобразиться без стилів адмінки або кине `KeyError`.
---

## §21. Datasets — пов'язані записи у ChangeForm

### Що таке Dataset

Datasets дозволяють вбудувати повноцінний ChangeList (список пов'язаних записів)
прямо у форму редагування батьківського об'єкта.

```python
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.contrib.inlines.admin import UnfoldStackedInline

# Замість стандартного Inline — Dataset (з пагінацією)
@admin.register(Note)
class NoteAdmin(UnfoldModelAdmin):
    # Tabs для форми
    fieldsets = [
        ('Основна інформація', {'tab': True, 'fields': ['title', 'body']}),
        ('Коментарі', {'tab': True, 'fields': []}),   # порожній fieldset для вкладки
    ]

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        extra = [
            path(
                '<int:note_id>/comments/',
                self.admin_site.admin_view(self.comments_dataset_view),
                name='hello_app_note_comments',
            ),
        ]
        return extra + urls

    def comments_dataset_view(self, request, note_id):
        """Часткова сторінка з коментарями для HTMX/iframe."""
        note = get_object_or_404(Note, pk=note_id)
        comments = note.comments.select_related('author').order_by('-created_at')
        paginator = Paginator(comments, 20)
        page_obj = paginator.get_page(request.GET.get('page', 1))
        return render(request, 'admin/hello_app/note/comments_dataset.html', {
            'note': note,
            'page_obj': page_obj,
            **self.admin_site.each_context(request),
        })
```

---

---
- **🧠 Ментальна модель:** Production Checklist — це "список перед зльотом". Пілоти не покладаються на пам'ять — вони завжди проходять checklist. Так само з production Django Admin: кожен пункт закриває конкретну категорію ризику (безпека, продуктивність, UX, архітектура). Пропуск будь-якого пункту — потенційна проблема у production.
- **📚 Чому ManifestStaticFilesStorage критичний:** Без ManifestStaticFilesStorage браузер кешує `main.css` агресивно (місяцями). Після деплою нової версії — користувачі бачать старі стилі, бо браузер показує кешовану версію. ManifestStaticFilesStorage додає hash до імені файлу: `main.02b59bcc.css`. При зміні файлу hash змінюється → нове ім'я → браузер завантажує нову версію. Стара version кешується нескінченно (cache-busting).
- **🌐 Що відбувається під капотом:** `collectstatic` з `ManifestStaticFilesStorage`: (1) збирає всі static файли у `STATIC_ROOT`, (2) обчислює MD5 hash кожного файлу, (3) створює копії з hash у імені: `main.css` → `main.02b59bcc.css`, (4) генерує `staticfiles.json` — маппінг `{'main.css': 'main.02b59bcc.css'}`. `{% static 'main.css' %}` → читає `staticfiles.json` → повертає `main.02b59bcc.css`.
- **❌ Типова помилка початківця:** Запустити production сервер з `DEBUG=True` "тимчасово". `DEBUG=True` у production означає: (1) Django показує traceback зі стеком викликів при кожній помилці (витік внутрішньої структури коду), (2) Django роздає static файли сам (повільно), (3) ALLOWED_HOSTS не перевіряється (вразливість Host header injection). Ніколи `DEBUG=True` у production.
---

## §22. Production Checklist

```
Django Admin + Unfold — Production Checklist
─────────────────────────────────────────────

БЕЗПЕКА
✅ Всі кастомні URL обгорнуті в admin_view()
✅ Перевірки прав у has_*_permission() методах
✅ format_html() замість mark_safe() для user-content
✅ search_fields не містять TEXT полів без індексів
✅ autocomplete_fields для великих FK
✅ Command Palette відключений або обмежений search_fields

ПРОДУКТИВНІСТЬ
✅ list_select_related для всіх FK у list_display
✅ prefetch_related у get_queryset() для M2M / зворотних FK
✅ InfinitePaginator для таблиць > 100k рядків
✅ search_fields з ^ або = префіксами (або get_search_results())
✅ Dashboard дані кешовані через cache.set/get (Redis)
✅ cached.Loader у TEMPLATES для production (APP_DIRS: False)
✅ ManifestStaticFilesStorage + collectstatic

АРХІТЕКТУРА
✅ Unfold встановлений ПЕРЕД django.contrib.admin в INSTALLED_APPS
✅ DASHBOARD_CALLBACK ізольований від view-логіки
✅ Component Classes для важких агрегацій на дашборді
✅ Кастомні сторінки через UnfoldModelAdminViewMixin
✅ Sidebar navigation оголошена в UNFOLD.SIDEBAR
✅ Немає HTML рядків у Python (тільки format_html())
✅ Немає прямих DB запитів у list_display методах (без select_related)

UX
✅ list_filter_submit = True для фільтрів з полями вводу
✅ warn_unsaved_form = True щоб попередити про незбережені зміни
✅ Fieldset tabs для форм з > 10 полями
✅ autocomplete_fields замість raw_id_fields (кращий UX)
✅ Unfold dark mode налаштований через THEME або CSS змінні
```
