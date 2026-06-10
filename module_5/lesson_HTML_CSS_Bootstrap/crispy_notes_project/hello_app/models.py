"""
models.py — Персональний менеджер записів

Скопійовано з lesson_Django_ORM_Database/notes_project.
У цьому проєкті акцент на Templates + Crispy Forms, а не на ORM.
Детальні коментарі до ORM: ../lesson_Django_ORM_Database/notes_project/hello_app/models.py

Архітектура (зв'язки між моделями):
    User ──1:1──► UserProfile
    User ──1:N──► Notebook, Note, Tag, TodoList, ShoppingList
    Notebook ──1:N──► Note        (SET_NULL)
    Note ──M:N──► Tag             (auto junction table)
    Note ──1:N──► Reminder        (CASCADE)
    TodoList ──1:N──► TodoItem    (CASCADE)
    ShoppingList ──1:N──► ShopItem (CASCADE)
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Profile({self.user.username})"

    class Meta:
        verbose_name = 'Профіль користувача'
        verbose_name_plural = 'Профілі користувачів'


class Tag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#808080')

    def __str__(self):
        return f"#{self.name}"

    class Meta:
        unique_together = [('user', 'name')]
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Notebook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notebooks')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#4A90E2')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        marker = " [Default]" if self.is_default else ""
        return f"{self.title}{marker}"

    class Meta:
        ordering = ['-is_default', 'title']
        verbose_name = 'Записник'
        verbose_name_plural = 'Записники'


class Note(models.Model):
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

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    notebook = models.ForeignKey(
        Notebook, on_delete=models.SET_NULL, null=True, blank=True, related_name='notes'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='notes')

    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    priority = models.PositiveSmallIntegerField(
        choices=PRIORITY_CHOICES,
        default=PRIORITY_LOW,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        pin = "📌 " if self.is_pinned else ""
        return f"{pin}{self.title}"

    class Meta:
        ordering = ['-is_pinned', '-priority', '-updated_at']
        verbose_name = 'Нотатка'
        verbose_name_plural = 'Нотатки'
        indexes = [
            models.Index(fields=['user', '-updated_at'], name='cnote_user_updated_idx'),
            models.Index(fields=['user', 'is_pinned'], name='cnote_user_pinned_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(priority__gte=1) & models.Q(priority__lte=4),
                name='cnote_priority_valid_range'
            ),
        ]


class Reminder(models.Model):
    REPEAT_CHOICES = [
        ('none', 'Без повторення'),
        ('daily', 'Щодня'),
        ('weekly', 'Щотижня'),
        ('monthly', 'Щомісяця'),
    ]

    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='reminders')
    remind_at = models.DateTimeField()
    message = models.CharField(max_length=500, blank=True)
    is_sent = models.BooleanField(default=False)
    repeat_pattern = models.CharField(max_length=20, choices=REPEAT_CHOICES, default='none')

    def __str__(self):
        return f"Нагадування для '{self.note.title}' о {self.remind_at:%d.%m %H:%M}"

    class Meta:
        ordering = ['remind_at']
        verbose_name = 'Нагадування'
        verbose_name_plural = 'Нагадування'


class TodoList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todo_lists')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='shared_todo_lists',
        blank=True,
        verbose_name='Поділитись з',
    )

    def __str__(self):
        return f"{'✅' if self.is_completed else '📋'} {self.title}"

    class Meta:
        ordering = ['is_completed', '-created_at']
        verbose_name = 'Список справ'
        verbose_name_plural = 'Списки справ'


class TodoItem(models.Model):
    todo_list = models.ForeignKey(TodoList, on_delete=models.CASCADE, related_name='items')
    text = models.CharField(max_length=500)
    is_done = models.BooleanField(default=False)
    order_position = models.PositiveIntegerField(default=0)
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{'☑' if self.is_done else '☐'} {self.text}"

    class Meta:
        ordering = ['order_position', 'id']


class ShoppingList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopping_lists')
    title = models.CharField(max_length=200)
    store_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='shared_shopping_lists',
        blank=True,
        verbose_name='Поділитись з',
    )

    def __str__(self):
        return f"🛒 {self.title}"

    class Meta:
        ordering = ['-created_at']


class ShopItem(models.Model):
    UNIT_CHOICES = [('шт', 'Штуки'), ('кг', 'Кілограми'), ('л', 'Літри'), ('г', 'Грами')]

    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1,
                                   validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=5, choices=UNIT_CHOICES, default='шт')
    is_purchased = models.BooleanField(default=False)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{'✓' if self.is_purchased else '○'} {self.name} ({self.quantity} {self.unit})"

    class Meta:
        ordering = ['is_purchased', 'name']
        constraints = [
            models.CheckConstraint(check=models.Q(quantity__gt=0), name='cshop_item_positive_qty'),
        ]
