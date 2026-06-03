"""
models.py — Схема бази даних для новинного порталу.

РОЛЬ У АРХІТЕКТУРІ:
    Моделі = Python-класи які Django ORM автоматично перетворює на SQL-таблиці.
    Це "єдине джерело істини" про структуру даних.

    Category → Article (один-до-багатьох: одна категорія, багато статей)

    Схема БД:
        news_category (id, name, slug, created_at)
              ↑ ForeignKey
        news_article  (id, title, content, source_url, pub_date,
                       is_published, created_at, updated_at, category_id)

ЯК ПРАЦЮЄ ORM:
    class Article(models.Model):   ← Python клас
        title = CharField(...)     ← поле моделі → SQL стовпець
                                   ← Django генерує: ALTER TABLE ADD COLUMN title VARCHAR(300)

    Article.objects.all()          ← QuerySet API → SELECT * FROM news_article
    Article.objects.filter(...)    ← WHERE ...

ПІСЛЯ ЗМІНИ МОДЕЛЕЙ — обов'язково:
    python manage.py makemigrations   ← фіксує план змін у файл
    python manage.py migrate          ← виконує SQL в БД
"""

from django.db import models
from django.utils import timezone
from django.utils.text import slugify


# ── Модель категорії ───────────────────────────────────────────────────────────

class Category(models.Model):
    """
    Категорія новини: Політика, Економіка, Суспільство тощо.

    SQL таблиця: news_category
    Зв'язок: 1 Category → N Articles (через ForeignKey в Article)
    """

    # CharField → VARCHAR в SQL (обмежена довжина рядка)
    name = models.CharField(
        max_length=100,
        unique=True,         # Не може бути двох категорій з однаковою назвою
        verbose_name='Назва' # Відображається в адмін-панелі
    )

    # SlugField → VARCHAR з обмеженням символів (a-z, 0-9, -)
    # Використовується в URL: /category/ekonomika/ замість /category/5/
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,          # Дозволяємо пустий рядок (заповнимо в save())
        verbose_name='URL-slug'
    )

    # DateTimeField → TIMESTAMP у SQL
    # auto_now_add=True → автоматично встановлюється при створенні запису
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Створено'
    )

    def save(self, *args, **kwargs):
        """Автоматично генеруємо slug з назви при збереженні."""
        if not self.slug:
            # slugify('Економіка') → 'ekonomika' (транслітерація + нижній регістр)
            # allow_unicode=True → зберігає кирилицю: 'економіка'
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        """Рядкове представлення об'єкта — відображається в адмін-панелі."""
        return self.name

    class Meta:
        # Meta клас налаштовує поведінку моделі на рівні таблиці
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'
        ordering = ['name']  # Сортування за замовчуванням: за алфавітом


# ── Модель статті ──────────────────────────────────────────────────────────────

class Article(models.Model):
    """
    Новинна стаття.

    SQL таблиця: news_article
    Зв'язок з Category: ForeignKey (багато статей → одна категорія)
    """

    # ForeignKey = зовнішній ключ → зв'язок "багато-до-одного"
    # Одна категорія може мати БАГАТО статей.
    # on_delete=SET_NULL: якщо категорія видалена → category_id = NULL
    # (стаття залишається, але без категорії)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,               # SQL: дозволяє NULL
        blank=True,              # Django форми: поле необов'язкове
        related_name='articles', # Article.category → Category
                                 # Category.articles.all() → всі статті категорії
        verbose_name='Категорія'
    )

    # Заголовок статті
    title = models.CharField(
        max_length=300,
        verbose_name='Заголовок'
    )

    # Текст статті (необов'язковий — статті з парсера можуть не мати тексту)
    content = models.TextField(
        blank=True,
        default='',
        verbose_name='Текст статті'
    )

    # URLField → спеціальний CharField з валідацією URL
    # null=True → може бути NULL якщо стаття введена вручну
    source_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        unique=True,   # Унікальний URL → захист від дублювання при парсингу
        verbose_name='Посилання на джерело'
    )

    # Назва джерела (rbc.ua, укрінформ тощо)
    source_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Джерело'
    )

    # Дата публікації статті на сайті-джерелі
    # null=True → при парсингу rbc.ua дата може бути недоступна
    pub_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата публікації'
    )

    # BooleanField → BOOLEAN у SQL (True/False)
    # Адмін модерує статті: False = чернетка, True = опублікована
    is_published = models.BooleanField(
        default=False,  # Нові статті спочатку — чернетки (модерація!)
        verbose_name='Опублікована'
    )

    # auto_now_add=True → тільки при створенні
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Додано до бази'
    )

    # auto_now=True → оновлюється при КОЖНОМУ save()
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Оновлено'
    )

    def __str__(self):
        return self.title[:80]  # Перші 80 символів заголовку

    class Meta:
        verbose_name = 'Стаття'
        verbose_name_plural = 'Статті'
        # Сортування за замовчуванням: нові статті першими
        # '-' перед полем = DESC (спадний порядок)
        ordering = ['-pub_date', '-created_at']

        # Складений індекс: прискорює запити з фільтрацією по категорії і статусу
        # SELECT * FROM news_article WHERE category_id=3 AND is_published=true
        indexes = [
            models.Index(fields=['category', 'is_published']),
            models.Index(fields=['-pub_date']),
        ]
