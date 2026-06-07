"""
models.py — Персональний менеджер записів

════════════════════════════════════════════════════════════════════
АРХІТЕКТУРА (зв'язки між моделями):
════════════════════════════════════════════════════════════════════

    User ──1:1──► UserProfile        (OneToOneField — вертикальне партиціонування)
    User ──1:N──► Notebook           (ForeignKey — записники)
    User ──1:N──► Note               (ForeignKey — нотатки)
    User ──1:N──► Tag                (ForeignKey — теги)
    User ──1:N──► TodoList           (ForeignKey — списки справ)
    User ──1:N──► ShoppingList       (ForeignKey — списки покупок)

    Notebook ──1:N──► Note           (ForeignKey SET_NULL — нотатки в записнику)
    Note ──M:N──► Tag                (ManyToManyField — мітки)
    Note ──1:N──► Reminder           (ForeignKey CASCADE — нагадування)

    TodoList ──1:N──► TodoItem       (ForeignKey CASCADE — пункти)
    ShoppingList ──1:N──► ShopItem   (ForeignKey CASCADE — товари)

════════════════════════════════════════════════════════════════════
ЩО ДЕМОНСТРУЄТЬСЯ:
════════════════════════════════════════════════════════════════════
    OneToOneField   → UserProfile (1:1)
    ForeignKey      → Notebook, Reminder, TodoItem, ShopItem (1:N)
    ManyToManyField → Tag ↔ Note (M:N, Django автоматично junction table)
    on_delete варіанти: CASCADE, SET_NULL
    choices (Enum-pattern)
    DecimalField для грошей (не FloatField!)
    Meta.indexes (B-Tree для типових запитів)
    Meta.constraints (UniqueConstraint + CheckConstraint)
    auto_now_add vs auto_now (timestamps)

════════════════════════════════════════════════════════════════════
КОМАНДИ:
════════════════════════════════════════════════════════════════════
    python manage.py makemigrations hello_app
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver
    # Відкрий: http://127.0.0.1:8000/admin/
"""

from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# ─────────────────────────────────────────────────────────────────────────────
# 1. USER PROFILE — розширення стандартного User (1:1)
# ─────────────────────────────────────────────────────────────────────────────

class UserProfile(models.Model):
    """
    Розширення вбудованого User через OneToOneField.

    Чому не додавати поля прямо до User?
    User — системна модель Django. Не чіпай її.
    Завжди розширюй через Profile або CustomUser.

    Чому OneToOneField а не ForeignKey?
    OneToOneField = ForeignKey + UNIQUE constraint.
    Гарантує: кожен User → максимум ОДИН Profile.

    Вертикальне партиціонування:
    User: 5 базових полів (username, email, password, ...)
    UserProfile: 20 додаткових полів (bio, city, timezone, ...)
    Запити що не потребують профілю → читають тільки User (вузька таблиця).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,    # видалення User → видалення Profile
        related_name='profile'       # user.profile — зворотній доступ
    )
    display_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text='Наприклад: Europe/Kyiv, UTC'
    )
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Profile({self.user.username})"

    class Meta:
        verbose_name = 'Профіль користувача'
        verbose_name_plural = 'Профілі користувачів'


# ─────────────────────────────────────────────────────────────────────────────
# 2. TAG — мітки для нотаток (M:N через ManyToManyField)
# ─────────────────────────────────────────────────────────────────────────────

class Tag(models.Model):
    """
    Теги для нотаток. Один тег може бути у багатьох нотатках.
    Одна нотатка може мати багато тегів → M:N зв'язок.

    Теги прив'язані до конкретного user:
    Alice може мати тег #робота, Bob теж може мати #робота,
    але це РІЗНІ теги (privacy між користувачами).

    unique_together = [('user', 'name')]:
    Alice не може мати два теги '#python' — але Alice і Bob можуть.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tags'
    )
    name = models.CharField(max_length=50)
    color = models.CharField(
        max_length=7,
        default='#808080',
        help_text='HEX колір: #FF5733'
    )

    def __str__(self):
        return f"#{self.name}"

    class Meta:
        unique_together = [('user', 'name')]   # Alice не може мати два '#python'
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


# ─────────────────────────────────────────────────────────────────────────────
# 3. NOTEBOOK — записник (контейнер для нотаток)
# ─────────────────────────────────────────────────────────────────────────────

class Notebook(models.Model):
    """
    Записник — колекція нотаток (як "папка").

    1:N зв'язок: Notebook → Note
    FK живе в Note (note.notebook_id), не в Notebook!
    Чому? Бо нотаток може бути "багато" → FK на стороні Many.

    is_default: нові нотатки потрапляють сюди без явного вибору.
    color: HEX колір для UI (різні кольори → різні записники).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notebooks'
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#4A90E2')
    is_default = models.BooleanField(
        default=False,
        help_text='Новi нотатки потрапляють у цей записник за замовчуванням'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        marker = " [Default]" if self.is_default else ""
        return f"{self.title}{marker}"

    class Meta:
        ordering = ['-is_default', 'title']
        verbose_name = 'Записник'
        verbose_name_plural = 'Записники'


# ─────────────────────────────────────────────────────────────────────────────
# 4. NOTE — головна сутність
# ─────────────────────────────────────────────────────────────────────────────

class Note(models.Model):
    """
    Нотатка — центральна сутність проекту.

    ═══ Зв'язки ═══
    user       → ForeignKey(User, CASCADE)      — автор (обов'язковий)
    notebook   → ForeignKey(Notebook, SET_NULL) — записник (опційний, nullable!)
    tags       → ManyToManyField(Tag)            — теги (M:N, junction table)

    ═══ Чому notebook nullable? ═══
    Нотатка може існувати без записника ("Без категорії").
    При видаленні Notebook → note.notebook = NULL (не видаляємо нотатку).
    on_delete=SET_NULL + null=True + blank=True — стандартний патерн.

    ═══ Чому tags через ManyToManyField? ═══
    Один тег у багатьох нотатках. Одна нотатка — багато тегів.
    Django автоматично створить: hello_app_note_tags (note_id FK, tag_id FK).
    note.tags.add(tag) → INSERT у junction table.
    note.tags.all() → JOIN через junction table.

    ═══ Meta.indexes ═══
    Типовий запит: filter(user=X, is_archived=False).order_by('-updated_at')
    → Index(fields=['user', '-updated_at']) покриває цей запит.
    """
    PRIORITY_LOW = 1
    PRIORITY_MEDIUM = 2
    PRIORITY_HIGH = 3
    PRIORITY_URGENT = 4

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, '🟢 Низький'),
        (PRIORITY_MEDIUM, '🟡 Середній'),
        (PRIORITY_HIGH, '🟠 Високий'),
        (PRIORITY_URGENT, '🔴 Терміново'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    notebook = models.ForeignKey(
        Notebook,
        on_delete=models.SET_NULL,    # видалення записника → note.notebook=NULL
        null=True,
        blank=True,
        related_name='notes'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='notes'
        # Django автоматично: CREATE TABLE hello_app_note_tags (note_id, tag_id)
    )

    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    priority = models.PositiveSmallIntegerField(
        choices=PRIORITY_CHOICES,
        default=PRIORITY_LOW,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    # auto_now_add: встановлюється ОДИН РАЗ при CREATE, більше не змінюється
    created_at = models.DateTimeField(auto_now_add=True)
    # auto_now: оновлюється при КОЖНОМУ save() — "last modified"
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        pin = "📌 " if self.is_pinned else ""
        return f"{pin}{self.title}"

    class Meta:
        # Сортування: закріплені першими, потім по пріоритету, потім нові
        ordering = ['-is_pinned', '-priority', '-updated_at']
        verbose_name = 'Нотатка'
        verbose_name_plural = 'Нотатки'
        indexes = [
            # Для типового запиту: нотатки юзера відсортовані по даті
            # filter(user=X, is_archived=False).order_by('-updated_at')
            models.Index(
                fields=['user', '-updated_at'],
                name='note_user_updated_idx'
            ),
            # Для пошуку закріплених
            models.Index(
                fields=['user', 'is_pinned'],
                name='note_user_pinned_idx'
            ),
        ]
        constraints = [
            # CHECK: priority від 1 до 4
            # Перевіряється навіть при прямому SQL (не тільки через Django!)
            models.CheckConstraint(
                check=models.Q(priority__gte=1) & models.Q(priority__lte=4),
                name='note_priority_valid_range'
            ),
        ]


# ─────────────────────────────────────────────────────────────────────────────
# 5. REMINDER — нагадування до нотатки
# ─────────────────────────────────────────────────────────────────────────────

class Reminder(models.Model):
    """
    Нагадування прив'язане до конкретної нотатки.

    1:N: одна нотатка може мати кілька нагадувань.
    on_delete=CASCADE: видалення нотатки → видалення всіх нагадувань.

    is_sent: щоб Celery task відправив тільки ОДИН раз.
    repeat_pattern: щодня, щотижня, ніколи.
    """
    REPEAT_NONE = 'none'
    REPEAT_DAILY = 'daily'
    REPEAT_WEEKLY = 'weekly'
    REPEAT_MONTHLY = 'monthly'

    REPEAT_CHOICES = [
        (REPEAT_NONE, 'Без повторення'),
        (REPEAT_DAILY, 'Щодня'),
        (REPEAT_WEEKLY, 'Щотижня'),
        (REPEAT_MONTHLY, 'Щомісяця'),
    ]

    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,    # note видалено → reminder теж
        related_name='reminders'
    )
    remind_at = models.DateTimeField()
    message = models.CharField(max_length=500, blank=True)
    is_sent = models.BooleanField(default=False)
    repeat_pattern = models.CharField(
        max_length=20,
        choices=REPEAT_CHOICES,
        default=REPEAT_NONE
    )

    def __str__(self):
        return f"Нагадування для '{self.note.title}' о {self.remind_at:%d.%m %H:%M}"

    class Meta:
        ordering = ['remind_at']
        indexes = [
            # Для Celery worker: знайти нагадування що треба відправити
            models.Index(
                fields=['is_sent', 'remind_at'],
                name='reminder_pending_idx'
            ),
        ]
        verbose_name = 'Нагадування'
        verbose_name_plural = 'Нагадування'


# ─────────────────────────────────────────────────────────────────────────────
# 6. TODO LIST + TODO ITEM — список справ
# ─────────────────────────────────────────────────────────────────────────────

class TodoList(models.Model):
    """
    Список справ — окрема сутність від Note.

    Чому не просто Note з галочками?
    TodoItem має is_done, order_position, due_date — це специфічні поля.
    Загальний "Universal Item" з 10 nullable полями — антипатерн.
    Окрема модель → чіткий API, типізовані поля.

    completion_percent(): розрахункова властивість — не зберігається в БД.
    Обчислюється через annotate() в selectors.py (не N+1!).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='todo_lists'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "✅" if self.is_completed else "📋"
        return f"{status} {self.title}"

    class Meta:
        ordering = ['is_completed', '-created_at']
        verbose_name = 'Список справ'
        verbose_name_plural = 'Списки справ'


class TodoItem(models.Model):
    """
    Один пункт у списку справ.

    order_position: для drag-and-drop сортування (позиція 1,2,3,...).
    due_date: nullable date — deadline для конкретного пункту.

    ForeignKey CASCADE: видалення TodoList → видалення всіх пунктів.
    """
    todo_list = models.ForeignKey(
        TodoList,
        on_delete=models.CASCADE,
        related_name='items'
    )
    text = models.CharField(max_length=500)
    is_done = models.BooleanField(default=False)
    order_position = models.PositiveIntegerField(default=0)
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        check = "☑" if self.is_done else "☐"
        return f"{check} {self.text}"

    class Meta:
        ordering = ['order_position', 'id']
        verbose_name = 'Пункт списку справ'
        verbose_name_plural = 'Пункти списків справ'


# ─────────────────────────────────────────────────────────────────────────────
# 7. SHOPPING LIST + SHOP ITEM — список покупок
# ─────────────────────────────────────────────────────────────────────────────

class ShoppingList(models.Model):
    """
    Список покупок — схожий на TodoList але зі специфічними полями для магазину.

    Чому окрема модель від TodoList?
    ShopItem: quantity, unit, estimated_price — якого немає у TodoItem.
    Кращий UX: різна UI, різні форми, різна логіка підрахунку суми.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_lists'
    )
    title = models.CharField(max_length=200)
    store_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"🛒 {self.title}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'


class ShopItem(models.Model):
    """
    Один товар у списку покупок.

    ═══ Чому DecimalField, а не FloatField? ═══
    FloatField → IEEE 754 binary float → 0.1 + 0.2 = 0.30000000000000004
    DecimalField → точна десяткова арифметика → 0.1 + 0.2 = 0.3
    ДЛЯ ГРОШЕЙ ЗАВЖДИ DecimalField!

    unit: choices для одиниць виміру (шт, кг, л, г).
    estimated_price: nullable — може не знати ціну заздалегідь.
    """
    UNIT_PIECES = 'шт'
    UNIT_KG = 'кг'
    UNIT_LITER = 'л'
    UNIT_GRAM = 'г'

    UNIT_CHOICES = [
        (UNIT_PIECES, 'Штуки'),
        (UNIT_KG, 'Кілограми'),
        (UNIT_LITER, 'Літри'),
        (UNIT_GRAM, 'Грами'),
    ]

    shopping_list = models.ForeignKey(
        ShoppingList,
        on_delete=models.CASCADE,
        related_name='items'
    )
    name = models.CharField(max_length=200)
    quantity = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(0)]
    )
    unit = models.CharField(
        max_length=5,
        choices=UNIT_CHOICES,
        default=UNIT_PIECES
    )
    is_purchased = models.BooleanField(default=False)
    estimated_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Орієнтовна ціна в UAH'
    )

    def __str__(self):
        check = "✓" if self.is_purchased else "○"
        return f"{check} {self.name} ({self.quantity} {self.unit})"

    class Meta:
        ordering = ['is_purchased', 'name']
        verbose_name = 'Товар'
        verbose_name_plural = 'Товари'
        constraints = [
            # CHECK: quantity > 0 (не можна купити 0 або від'ємну кількість)
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name='shop_item_positive_quantity'
            ),
        ]


# ─────────────────────────────────────────────────────────────────────────────
# QUERYSETS — ДОВІДНИК API
# ─────────────────────────────────────────────────────────────────────────────
"""
Основні QuerySet запити (всі вони ЛІНИВІ — SQL виконується тільки при evaluation!):

  # Отримати нотатки з FK та M:N (вирішення N+1):
  notes = Note.objects.select_related('user', 'notebook').prefetch_related('tags')

  # F() — атомарний інкремент (без race condition):
  Note.objects.filter(pk=1).update(views_count=F('views_count') + 1)

  # Агрегації:
  from django.db.models import Count, Sum
  Category.objects.annotate(note_count=Count('notes'))
  ShopItem.objects.filter(is_purchased=False).aggregate(total=Sum('estimated_price'))

  # transaction.atomic() — атомарна операція:
  with transaction.atomic():
      note = Note.objects.create(...)
      Reminder.objects.create(note=note, ...)

  # select_for_update() — блокування рядка:
  with transaction.atomic():
      item = TodoItem.objects.select_for_update().get(pk=item_id)
      item.is_done = not item.is_done
      item.save()
"""
