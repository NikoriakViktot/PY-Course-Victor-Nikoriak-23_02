"""
admin.py — Конфігурація адмін-панелі Django.

РОЛЬ У АРХІТЕКТУРІ:
    Адмін-панель — це готовий бек-офіс для управління контентом.
    Django автоматично генерує CRUD інтерфейс для кожної зареєстрованої моделі.

    URL: http://localhost:8000/admin/
    Доступ: тільки для staff/superuser акаунтів

ЩО РОБИТЬ admin.py:
    1. admin.site.register(Model) → стандартний інтерфейс
    2. @admin.register(Model) + клас → кастомізований інтерфейс

КАСТОМІЗАЦІЯ:
    list_display    → які поля показувати в таблиці списку
    list_filter     → фільтри в правій колонці
    search_fields   → поля для рядка пошуку
    list_editable   → редагування прямо в списку (без входу в форму)
    actions         → кастомні дії ("Опублікувати вибрані")
    prepopulated_fields → автозаповнення (slug ← title)
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Article


# ── Адмін для категорій ────────────────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Адмін-клас для моделі Category."""

    # Колонки в таблиці списку категорій
    list_display = ('name', 'slug', 'article_count', 'created_at')

    # Автозаповнення поля slug при введенні name
    # Користувач пише "Економіка" → slug автоматично: "ekonomika"
    prepopulated_fields = {'slug': ('name',)}

    # Поля для рядка пошуку
    search_fields = ('name',)

    def article_count(self, obj):
        """Показує кількість статей у цій категорії."""
        # obj.articles — це related_name з ForeignKey в Article
        # .count() → ефективний COUNT(*) в SQL (без завантаження всіх статей)
        return obj.articles.count()

    # Назва колонки в адмін-панелі
    article_count.short_description = 'Статей'


# ── Адмін для статей ───────────────────────────────────────────────────────────

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Адмін-клас для моделі Article з розширеними можливостями."""

    # Колонки в списку статей
    list_display = (
        'title',
        'category',
        'source_name',
        'is_published',
        'pub_date',
        'created_at',
        'source_link',  # наш кастомний метод нижче
    )

    # Фільтри в правій боковій панелі
    list_filter = (
        'is_published',  # фільтр: Так / Ні
        'category',      # фільтр: по категорії
        'source_name',   # фільтр: по джерелу
    )

    # Пошук за цими полями
    # '__' = обхід зв'язку: category__name → шукати в полі name таблиці Category
    search_fields = ('title', 'content', 'category__name')

    # Редагування прямо в списку (без відкриття форми)
    # Дозволяє швидко публікувати/відхиляти статті одним кліком
    list_editable = ('is_published',)

    # Сортування за замовчуванням в адмін-панелі
    ordering = ('-created_at',)

    # Розбивка на сторінки
    list_per_page = 25

    # Поля у формі редагування розбиті по секціях
    fieldsets = (
        ('Основна інформація', {
            'fields': ('title', 'category', 'content')
        }),
        ('Джерело', {
            'fields': ('source_url', 'source_name', 'pub_date'),
            # classes=('collapse',) → секція згорнута за замовчуванням
            'classes': ('collapse',),
        }),
        ('Публікація', {
            'fields': ('is_published',)
        }),
    )

    # Кастомні дії — з'являються в меню "Action" над списком
    actions = ['publish_selected', 'unpublish_selected']

    def publish_selected(self, request, queryset):
        """Опублікувати всі вибрані статті одразу."""
        # queryset.update() → один SQL запит UPDATE (ефективно!)
        # Замість циклу article.save() для кожної → N запитів
        count = queryset.update(is_published=True)
        self.message_user(request, f'Опубліковано {count} статей.')

    publish_selected.short_description = 'Опублікувати вибрані статті'

    def unpublish_selected(self, request, queryset):
        """Приховати всі вибрані статті."""
        count = queryset.update(is_published=False)
        self.message_user(request, f'Приховано {count} статей.')

    unpublish_selected.short_description = 'Приховати вибрані статті'

    def source_link(self, obj):
        """Відображає посилання на джерело як клікабельний HTML-тег."""
        if obj.source_url:
            # format_html() — безпечний спосіб вставити HTML у Django
            # (автоматично екранує небезпечні символи)
            return format_html(
                '<a href="{}" target="_blank">↗</a>',
                obj.source_url
            )
        return '—'

    source_link.short_description = 'Джерело'


# ── Налаштування адмін-сайту ────────────────────────────────────────────────────

# Змінюємо заголовки адмін-панелі на українські
admin.site.site_header = 'Новинний Портал — Адміністрування'
admin.site.site_title = 'Новинний Портал'
admin.site.index_title = 'Панель управління'
