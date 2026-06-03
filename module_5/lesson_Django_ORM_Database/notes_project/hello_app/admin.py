"""
admin.py — Django Admin для Notes Platform

════════════════════════════════════════════════════════════════════
ЩО ТАКЕ DJANGO ADMIN?
════════════════════════════════════════════════════════════════════

Django Admin — автоматичний CRUD інтерфейс для моделей.
Після реєстрації моделі: /admin/ → можна переглядати, додавати,
редагувати та видаляти записи без написання жодного View/Template!

Призначення: внутрішній інструмент для staff/superusers.
НЕ для звичайних користувачів (для них — Views + Templates).

Команди для старту:
  python manage.py createsuperuser  → створити admin акаунт
  python manage.py runserver        → запустити сервер
  Відкрий: http://127.0.0.1:8000/admin/

════════════════════════════════════════════════════════════════════
КЛЮЧОВІ ВЛАСТИВОСТІ ModelAdmin:
════════════════════════════════════════════════════════════════════

  list_display    → колонки у таблиці списку (що бачиш на /admin/model/)
  list_filter     → права панель фільтрів (фільтр по статусу тощо)
  search_fields   → поле пошуку вгорі таблиці
                    ^ = startswith, = = exact, @ = full-text search
  raw_id_fields   → замість dropdown → простий ID input (для великих таблиць)
  filter_horizontal → UI для ManyToManyField: два вікна з drag-and-drop
  readonly_fields → поля що тільки читаються (auto_now не можна редагувати!)
  inlines         → вбудовані форми для FK відносин (1:N в одній сторінці)
  ordering        → сортування за замовчуванням у list view
  list_per_page   → кількість записів на сторінці

  get_queryset()  → кастомізація основного QuerySet
                    → Тут додаємо select_related для уникнення N+1!

  @admin.display  → декоратор для методів що відображаються в list_display
  @admin.action   → декоратор для масових дій

════════════════════════════════════════════════════════════════════
UNFOLD ADMIN:
════════════════════════════════════════════════════════════════════

  unfold.admin.ModelAdmin замінює django.contrib.admin.ModelAdmin.
  Надає Tailwind CSS стилізований інтерфейс замість стандартного Django Admin.
  Теорія: module_5/lesson_Django_Network_Architecture/DJANGO_ADMIN_UNFOLD.md

  Все що робить стандартний ModelAdmin → робить і Unfold ModelAdmin,
  але з красивим сучасним UI.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django.db.models import Count

from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import (
    UserProfile,
    Notebook,
    Tag,
    Note,
    Reminder,
    TodoList,
    TodoItem,
    ShoppingList,
    ShopItem,
)


# ─────────────────────────────────────────────────────────────────────────────
# USER та GROUP — Заміна стандартних на Unfold-стилізовані
# ─────────────────────────────────────────────────────────────────────────────

# Крок 1: Скасовуємо стандартну реєстрацію (Django реєструє їх за замовчуванням)
admin.site.unregister(User)
admin.site.unregister(Group)


# Крок 2: Реєструємо знову, але з Unfold стилізацією
@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """
    Стандартний UserAdmin з Unfold стилізацією.

    BaseUserAdmin: вся логіка управління users (пароль, permissions тощо)
    ModelAdmin (Unfold): Tailwind CSS стилізація

    Multiple inheritance: Python MRO (Method Resolution Order) визначає
    що UserAdmin.form буде з BaseUserAdmin, але rendering — з Unfold ModelAdmin.
    """
    form = UserChangeForm            # Unfold стилізована форма зміни юзера
    add_form = UserCreationForm      # Unfold стилізована форма створення
    change_password_form = AdminPasswordChangeForm  # форма зміни пароля


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    """Стандартний GroupAdmin з Unfold стилізацією."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# USER PROFILE
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    """
    Адмін для UserProfile (1:1 розширення User).

    ════════════════════════════════════════════════════════════════
    raw_id_fields = ['user']
    ════════════════════════════════════════════════════════════════

    Без raw_id_fields: Django рендерить <select> з УСІМА юзерами.
      → 10,000 юзерів у БД → select завантажує всі → повільно!

    З raw_id_fields: рендерить <input type="text"> для введення ID
      + кнопка "пошук" що відкриває popup → вибрати юзера
      → Завантажує тільки вибраного юзера → швидко!

    Правило: raw_id_fields для всіх FK де таблиця може мати >100 рядків.
    """
    list_display    = ['user', 'display_name', 'timezone']
    search_fields   = [
        'user__username',    # __ traversal: profile → user.username
        'display_name',      # пряме поле профілю
    ]
    raw_id_fields   = ['user']  # ID input замість dropdown (для великих таблиць)
    list_per_page   = 25


# ─────────────────────────────────────────────────────────────────────────────
# TAG
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Tag)
class TagAdmin(ModelAdmin):
    """
    Адмін для тегів.

    ════════════════════════════════════════════════════════════════
    color_preview() → format_html()
    ════════════════════════════════════════════════════════════════

    format_html() — безпечне генерування HTML в Python.

    БЕЗ format_html (НЕБЕЗПЕЧНО):
      def color_preview(self, obj):
          return f'<span style="background:{obj.color}">&nbsp;</span>'
          # → XSS атака якщо obj.color містить JavaScript!

    З format_html (БЕЗПЕЧНО):
      return format_html('<span style="background:{c}">...</span>', c=obj.color)
      → Django автоматично екранує {c}: < → &lt; > → &gt; тощо
    """
    list_display  = ['name', 'user', 'color_preview']
    search_fields = [
        '^name',             # ^ = startswith (швидше за contains)
        'user__username',
    ]
    raw_id_fields = ['user']
    list_per_page = 50

    @admin.display(description='Колір')  # назва колонки у list_display
    def color_preview(self, obj):
        """
        Показує кольоровий квадрат у таблиці.

        format_html() безпечно генерує HTML:
          {c} → автоматично екранується (XSS захист!)
          Без format_html: звичайна f-string НЕ екранується!
        """
        return format_html(
            # {c} → значення obj.color, автоматично escaped
            '<span style="background:{c};padding:2px 14px;border-radius:4px;">'
            '&nbsp;</span>&nbsp;<code>{c}</code>',
            c=obj.color  # HEX рядок, наприклад "#3776AB"
        )


# ─────────────────────────────────────────────────────────────────────────────
# NOTEBOOK
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Notebook)
class NotebookAdmin(ModelAdmin):
    """
    Адмін для записників з лічильником нотаток.

    ════════════════════════════════════════════════════════════════
    get_queryset() + annotate() → уникнення N+1
    ════════════════════════════════════════════════════════════════

    Проблема N+1 без get_queryset():
      list_display = ['title', 'note_count']

      def note_count(self, obj):
          return obj.notes.count()   # ← окремий SELECT для КОЖНОГО рядка!
          # 50 записників → 50 + 1 = 51 SQL запит!

    Рішення: annotate у get_queryset():
      def get_queryset(self, request):
          return super().get_queryset().annotate(_note_count=Count('notes'))
          # 1 SQL з GROUP BY: SELECT notebook.*, COUNT(note.id) AS _note_count
          #                   GROUP BY notebook.id

      def note_count(self, obj):
          return obj._note_count  # вже в об'єкті, ніякого SELECT!
          # 50 записників → 1 SQL запит!

    ordering=('_note_count',) у @admin.display → можна сортувати по колонці!
    """
    list_display  = ['title', 'user', 'is_default', 'note_count', 'created_at']
    list_filter   = ['is_default', 'created_at']
    search_fields = ['^title', 'user__username']
    raw_id_fields = ['user']
    readonly_fields = ['created_at']  # auto_now_add → не можна редагувати
    list_per_page = 25

    def get_queryset(self, request):
        """
        Перевизначаємо QuerySet щоб додати annotate.

        super().get_queryset(request) → базовий QuerySet ModelAdmin
        .select_related('user') → уникнення N+1 для user (показується в list_display)
        .annotate(_note_count=Count('notes')) → GROUP BY для лічильника
        """
        return super().get_queryset(request).select_related('user').annotate(
            _note_count=Count('notes')
            # Count('notes') → COUNT(hello_app_note.id) GROUP BY notebook.id
            # Ім'я _note_count (з підкресленням) → не конфліктує з методом note_count
        )

    @admin.display(description='Нотаток', ordering='_note_count')
    def note_count(self, obj):
        """
        Відображає кількість нотаток.
        ordering='_note_count' → клік на колонку сортує по цьому полю.
        """
        return obj._note_count  # вже анотований у get_queryset()


# ─────────────────────────────────────────────────────────────────────────────
# NOTE (центральна модель)
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Note)
class NoteAdmin(ModelAdmin):
    """
    Адмін для нотаток — демонструє всі ключові Admin техніки.

    ════════════════════════════════════════════════════════════════
    filter_horizontal = ['tags'] — UI для ManyToManyField
    ════════════════════════════════════════════════════════════════

    Без filter_horizontal: стандартний <select multiple> (незручно!)
    З filter_horizontal: два вікна side-by-side:
      Ліве: "Доступні теги"   Праве: "Обрані теги"
      → drag-and-drop або подвійний клік для переміщення
      → Набагато зручніший UX для M:N полів

    ════════════════════════════════════════════════════════════════
    select_related в get_queryset → N+1 prevention
    ════════════════════════════════════════════════════════════════

    list_display включає 'user' та 'notebook'.
    При рендері кожного рядка: note.user, note.notebook → FK → SELECT!
    50 нотаток → 50 SELECT для user + 50 SELECT для notebook = 101 запит!

    get_queryset() з select_related → 1 SQL з двома JOIN → завжди!
    """
    list_display = [
        'title', 'user', 'notebook', 'priority_display',
        'is_pinned', 'is_archived', 'updated_at'
    ]
    filter_horizontal = ['tags']   # M:N поле → зручний UI
    list_filter = [
        'priority',      # фільтр по пріоритету (dropdown з choices)
        'is_pinned',     # фільтр "Так/Ні"
        'is_archived',   # фільтр "Так/Ні"
        'created_at',    # DateFieldListFilter → "Сьогодні/Цей тиждень/..."
    ]
    search_fields = [
        '^title',         # ^ = починається з (ефективніше для title)
        'content',        # = contains (повний LIKE)
        'user__username', # traversal FK: user → username
    ]
    raw_id_fields   = ['user', 'notebook']
    readonly_fields = ['created_at', 'updated_at']  # auto_now поля!
    list_per_page   = 20
    ordering        = ['-updated_at']  # сортування за замовчуванням

    def get_queryset(self, request):
        """
        select_related для уникнення N+1 у list_display.

        Без select_related:
          50 нотаток × (1 SELECT для user + 1 SELECT для notebook) = 101 запит!

        З select_related:
          1 SELECT з двома LEFT JOIN → все в одному запиті.

        SQL:
          SELECT note.*, u.username, nb.title
          FROM hello_app_note note
          LEFT JOIN auth_user u ON note.user_id = u.id
          LEFT JOIN hello_app_notebook nb ON note.notebook_id = nb.id
        """
        return super().get_queryset(request).select_related('user', 'notebook')

    @admin.display(description='Пріоритет', ordering='priority')
    def priority_display(self, obj):
        """
        Відображає пріоритет з кольоровим emoji.
        ordering='priority' → клік на колонку сортує по числовому значенню.

        get_priority_display() → Django автоматично генерує цей метод
        для полів з choices! Повертає human-readable назву.
        obj.priority = 2 → obj.get_priority_display() = '🟡 Середній'
        """
        icons = {1: '🟢', 2: '🟡', 3: '🟠', 4: '🔴'}
        return format_html(
            '{} {}',
            icons.get(obj.priority, '?'),  # emoji по числовому значенню
            obj.get_priority_display()     # human-readable з choices
        )


# ─────────────────────────────────────────────────────────────────────────────
# REMINDER
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Reminder)
class ReminderAdmin(ModelAdmin):
    """
    Адмін для нагадувань.

    is_sent + remind_at фільтри → корисно для debugging Celery tasks:
    "Чому нагадування не відправилось?"
      → list_filter is_sent=False, remind_at=[вчора]
      → бачимо всі незалежно від часу
    """
    list_display  = ['note', 'remind_at', 'is_sent', 'repeat_pattern']
    list_filter   = [
        'is_sent',         # "Відправлено? Так/Ні"
        'repeat_pattern',  # "Тип повторення"
        'remind_at',       # "Коли?" (DateField filter)
    ]
    search_fields = ['note__title', 'message']
    raw_id_fields = ['note']
    list_per_page = 30

    def get_queryset(self, request):
        """
        select_related('note', 'note__user'):
          Traversal через дві FK: reminder → note → user
          note.title і note.user.username доступні без додаткових запитів.
        """
        return super().get_queryset(request).select_related('note', 'note__user')


# ─────────────────────────────────────────────────────────────────────────────
# TODO LIST + TODO ITEM (Inline)
# ─────────────────────────────────────────────────────────────────────────────

class TodoItemInline(TabularInline):
    """
    TabularInline: редагувати TodoItem прямо на сторінці TodoList!

    ════════════════════════════════════════════════════════════════
    ЩО ТАКЕ INLINE?
    ════════════════════════════════════════════════════════════════

    Inline відображає пов'язані об'єкти (FK) прямо на сторінці батьківського об'єкту.
    Замість: окрема сторінка для кожного TodoItem
    Inline:  все на одній сторінці TodoList → зручно!

    TabularInline: кожен рядок = один запис (таблична форма)
    StackedInline: кожен запис — вертикальний блок полів (широкі форми)

    extra = 2 → показує 2 порожніх рядки для нових записів
    fields → які поля показувати в inline таблиці
    """
    model = TodoItem  # модель що буде відображатись як inline
    extra = 2         # кількість порожніх рядків для нових пунктів
    fields = ['text', 'is_done', 'order_position', 'due_date']


@admin.register(TodoList)
class TodoListAdmin(ModelAdmin):
    """
    Адмін для списків справ з inlines.

    inlines = [TodoItemInline] → на сторінці TodoList буде таблиця TodoItem!
    Можна редагувати і список і пункти одночасно.
    """
    list_display    = ['title', 'user', 'is_completed', 'item_count', 'created_at']
    list_filter     = ['is_completed', 'created_at']
    search_fields   = ['^title', 'user__username']
    raw_id_fields   = ['user']
    readonly_fields = ['created_at']
    inlines         = [TodoItemInline]  # ← вбудована форма для пунктів!
    list_per_page   = 20

    def get_queryset(self, request):
        """
        annotate(_item_count=Count('items')):
        Додаємо COUNT в один GROUP BY запит.
        Уникаємо N+1 у методі item_count().
        """
        return super().get_queryset(request).select_related('user').annotate(
            _item_count=Count('items')
        )

    @admin.display(description='Пунктів', ordering='_item_count')
    def item_count(self, obj):
        """
        Читає _item_count що вже анотований у get_queryset().
        Ніякого додаткового SELECT!
        """
        return obj._item_count


# ─────────────────────────────────────────────────────────────────────────────
# SHOPPING LIST + SHOP ITEM (Inline + масова дія)
# ─────────────────────────────────────────────────────────────────────────────

class ShopItemInline(TabularInline):
    """
    TabularInline для товарів у списку покупок.
    extra=3 → три порожніх рядки (зазвичай додають кілька товарів одразу).
    """
    model  = ShopItem
    extra  = 3
    fields = ['name', 'quantity', 'unit', 'estimated_price', 'is_purchased']


@admin.register(ShoppingList)
class ShoppingListAdmin(ModelAdmin):
    """
    Адмін для списків покупок.

    ════════════════════════════════════════════════════════════════
    @admin.action — масові дії
    ════════════════════════════════════════════════════════════════

    actions = ['mark_all_purchased'] → з'являється dropdown "Дії" над таблицею
    Користувач: вибирає декілька списків → "Позначити товари як куплені" → Apply

    @admin.action(description=...) → назва у dropdown

    В методі:
      ShopItem.objects.filter(shopping_list__in=queryset).update(is_purchased=True)
      → Один SQL UPDATE для ВСІХ товарів ВСІХ обраних списків!
      → filter(shopping_list__in=queryset) → SQL: WHERE shopping_list_id IN (1, 2, 3)

      self.message_user(request, "...") → показує повідомлення після дії
    """
    list_display    = ['title', 'user', 'store_name', 'item_count', 'created_at']
    search_fields   = ['^title', 'user__username', 'store_name']
    raw_id_fields   = ['user']
    readonly_fields = ['created_at']
    inlines         = [ShopItemInline]
    list_per_page   = 20
    actions         = ['mark_all_purchased']  # реєструємо масову дію

    def get_queryset(self, request):
        """
        annotate для кількості товарів (уникнення N+1).
        """
        return super().get_queryset(request).select_related('user').annotate(
            _item_count=Count('items')
        )

    @admin.display(description='Товарів', ordering='_item_count')
    def item_count(self, obj):
        return obj._item_count

    @admin.action(description='Позначити всі товари як куплені')
    def mark_all_purchased(self, request, queryset):
        """
        Масова дія: позначити всі товари обраних списків як куплені.

        queryset: QuerySet[ShoppingList] — обрані списки

        Крок 1: ShopItem.objects.filter(shopping_list__in=queryset)
          → FK traversal: знаходимо товари що належать обраним спискам
          SQL WHERE: shopping_list_id IN (SELECT id FROM shoppinglist WHERE ...)

        Крок 2: .update(is_purchased=True)
          → Один SQL UPDATE для всіх знайдених товарів
          SQL: UPDATE shopitem SET is_purchased = TRUE WHERE shopping_list_id IN (...)
          → Набагато ефективніше ніж: for item in items: item.save()

        Крок 3: self.message_user(request, message)
          → Показує зелений банер-повідомлення у admin панелі
        """
        # Масовий UPDATE одним SQL запитом
        updated = ShopItem.objects.filter(
            shopping_list__in=queryset  # FK traversal: всі товари обраних списків
        ).update(is_purchased=True)

        # Показуємо повідомлення про успіх
        self.message_user(
            request,
            f'Позначено {updated} товарів як куплені.'
        )
