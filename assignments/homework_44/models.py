from django.db import models
from django.contrib.auth.models import User
class NoteGroup(models.Model):
    title = models.CharField(max_length=100, verbose_name="Назва групи")
    members = models.ManyToManyField(User, related_name='note_groups', verbose_name="Учасники групи")
    def __str__(self):
        return self.title
class Category(models.Model):
    title = models.CharField(max_length=100, verbose_name="Назва категорії")
    def __str__(self):
        return self.title
class Note(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст нотатки")
    reminder = models.DateTimeField(null=True, blank=True, verbose_name="Нагадування")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='notes', verbose_name="Категорія")
    # Вказівка на автора нотатки
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_notes', verbose_name="Автор")
    # Поле для групових нотаток (Extra)
    group = models.ForeignKey(NoteGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='group_notes',
                              verbose_name="Група")
    def __str__(self):
        return self.title