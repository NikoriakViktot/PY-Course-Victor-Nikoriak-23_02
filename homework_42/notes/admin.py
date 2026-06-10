from django.contrib import admin

from .models import Category, Note


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "category",
        "group",
        "reminder",
        "created_at",
        "telegram_sent_at",
        "reminder_telegram_sent_at",
        "updated_at",
    )
    list_filter = (
        "owner",
        "group",
        "category",
        "reminder",
        "telegram_sent_at",
        "reminder_telegram_sent_at",
        "created_at",
    )
    search_fields = ("title", "text", "owner__username", "group__name")
    date_hierarchy = "created_at"
    autocomplete_fields = ("owner", "category", "group")