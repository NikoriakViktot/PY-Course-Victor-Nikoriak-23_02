from django.contrib import admin
from .models import Note  # імпортуємо нашу модель


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    # Які колонки показувати в таблиці списку
    list_display = ('title', 'created_at')

    # Поля для рядка пошуку
    search_fields = ('title', 'content')