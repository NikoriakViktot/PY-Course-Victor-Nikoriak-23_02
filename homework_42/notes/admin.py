from django.contrib import admin
from .models import Category, Note


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "reminder", "created_at", "updated_at")
    list_filter = ("category", "reminder", "created_at")
    search_fields = ("title","text")
    date_hierarchy = "created_at"