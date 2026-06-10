from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html

# unfold.admin.ModelAdmin замінює стандартний django.contrib.admin.ModelAdmin.
# Дає Tailwind-стилізований інтерфейс замість базового Django Admin.
# Теорія: DJANGO_ADMIN_UNFOLD.md §2 — ModelAdmin.
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import Note


# ── User і Group ─────────────────────────────────────────────────────────────
# Django реєструє User і Group через власні AdminClass без Unfold.
# Знімаємо стандартну реєстрацію і додаємо з Unfold-стилем.
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Перевизначаємо стандартні форми на Unfold-версії (інакше форма без стилів)
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


# ── Note ──────────────────────────────────────────────────────────────────────
@admin.register(Note)
class NoteAdmin(ModelAdmin):
    """
    Кастомний ModelAdmin для Note з Unfold-стилізацією.
    Теорія: DJANGO_ADMIN_UNFOLD.md §2 — ModelAdmin attributes.
    """

    list_display = ['title', 'short_content', 'created_at']
    search_fields = ['^title', 'content']  # ^ = startswith, використовує індекс
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    list_per_page = 20

    @admin.display(description='Зміст (preview)')
    def short_content(self, obj):
        if not obj.content:
            return '—'
        preview = obj.content[:80] + ('...' if len(obj.content) > 80 else '')
        # format_html екранує значення — безпечно для user-content
        return format_html('<span style="color:#6b7280">{}</span>', preview)
