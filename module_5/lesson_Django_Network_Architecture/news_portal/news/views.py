"""
views.py — Бізнес-логіка новинного порталу.

РОЛЬ У АРХІТЕКТУРІ:
    View = центральний оркестратор HTTP-запиту.
    Отримує HttpRequest → запитує БД → повертає HttpResponse (HTML).

    Схема:  urls.py → views.py → models.py (ORM) → templates/ → HTML

ТИП В'ЮШ У ЦЬОМУ ПРОЄКТІ:
    Ми використовуємо Generic Class-Based Views (CBV) — вбудовані Django-класи
    для типових операцій читання даних (списки, деталі).

    ListView    → GET /           → список всіх опублікованих статей
    DetailView  → GET /article/5/ → детальна сторінка однієї статті
    ListView    → GET /category/ekonomika/ → статті певної категорії

ЧОМУ CBV, А НЕ FBV?
    Generic Views автоматизують:
    - пагінацію (paginate_by)
    - вибірку об'єктів (get_queryset)
    - передачу контексту в шаблон

    FBV (Function-Based Views) гнучкіші, але потребують більше коду.
    Для CRUD читання CBV ідеальні.

АНАЛОГІЯ: Шеф-кухар — отримує замовлення (request),
          бере інгредієнти з комори (ORM), готує страву і видає клієнту (HTML).
"""

from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404

from .models import Article, Category


# ── Список новин (головна сторінка) ────────────────────────────────────────────

class ArticleListView(ListView):
    """
    GET / → Список опублікованих статей, нові першими.

    ListView автоматично:
        1. Викликає get_queryset() → отримує список об'єктів
        2. Застосовує пагінацію (paginate_by)
        3. Передає об'єкти в шаблон як context['article_list']
        4. Рендерить template_name
    """

    # Яку модель показуємо
    model = Article

    # Назва шаблону (шукається в templates/ )
    template_name = 'news/article_list.html'

    # Ім'я змінної в шаблоні: {{ article_list }}
    # (за замовчуванням Django додає _list суфікс)
    context_object_name = 'articles'

    # Кількість статей на сторінці (автоматична пагінація)
    paginate_by = 10

    def get_queryset(self):
        """
        Повертає QuerySet тільки опублікованих статей.

        select_related('category') → JOIN з таблицею категорій ОДНИМ запитом.
        БЕЗ select_related: для кожної статті в циклі → окремий SQL запит (N+1!)
        З select_related: 1 SQL SELECT з JOIN → всі дані одразу.
        """
        return (
            Article.objects
            .filter(is_published=True)
            # JOIN: SELECT ... FROM news_article
            #       INNER JOIN news_category ON news_article.category_id = news_category.id
            .select_related('category')
            # Сортування: по даті публікації (DESC), потім по даті створення (DESC)
            .order_by('-pub_date', '-created_at')
        )

    def get_context_data(self, **kwargs):
        """
        Додає додаткові дані в контекст шаблону.

        get_context_data() викликається після get_queryset().
        super() → Django заповнює базовий контекст (paginator, page_obj тощо).
        Ми додаємо свої дані зверху.
        """
        # Спочатку отримуємо базовий контекст від ListView
        context = super().get_context_data(**kwargs)

        # Додаємо список категорій для навігаційного меню
        # Сортуємо за алфавітом (визначено в Category.Meta.ordering)
        context['categories'] = Category.objects.all()

        # Заголовок сторінки для тегу <title>
        context['page_title'] = 'Всі новини'

        return context


# ── Деталі статті ──────────────────────────────────────────────────────────────

class ArticleDetailView(DetailView):
    """
    GET /article/<pk>/ → Повна стаття.

    DetailView автоматично:
        1. Знаходить об'єкт за pk (або slug) з URL
        2. Якщо не знайдено → повертає 404
        3. Передає об'єкт в шаблон як context['article']
    """

    model = Article
    template_name = 'news/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        """Дозволяємо переглядати тільки опубліковані статті."""
        return (
            Article.objects
            .filter(is_published=True)
            # JOIN для отримання даних категорії разом зі статтею
            .select_related('category')
        )

    def get_context_data(self, **kwargs):
        """Додаємо список категорій для навігаційного меню."""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


# ── Статті за категорією ────────────────────────────────────────────────────────

class CategoryArticleListView(ListView):
    """
    GET /category/<slug>/ → Статті конкретної категорії.

    Наслідуємо від ArticleListView але фільтруємо по категорії.
    """

    model = Article
    template_name = 'news/article_list.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        """
        Отримуємо категорію з URL-параметру та фільтруємо статті.

        self.kwargs['slug'] → значення захопленого URL-параметру
        Наприклад: /category/ekonomika/ → self.kwargs['slug'] = 'ekonomika'

        get_object_or_404() → якщо категорія не існує → HTTP 404 (не 500)
        """
        # Зберігаємо категорію в self для використання в get_context_data
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['slug']
        )

        return (
            Article.objects
            .filter(
                category=self.category,
                is_published=True
            )
            .select_related('category')
            .order_by('-pub_date', '-created_at')
        )

    def get_context_data(self, **kwargs):
        """Додаємо поточну категорію і список всіх категорій."""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()

        # Передаємо поточну категорію для виділення в навігації
        context['current_category'] = self.category
        context['page_title'] = self.category.name

        return context
