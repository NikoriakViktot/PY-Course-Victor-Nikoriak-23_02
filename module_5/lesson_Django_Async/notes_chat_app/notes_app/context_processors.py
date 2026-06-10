"""
context_processors.py — глобальні змінні шаблону

Sidebar data (notebooks + tags) available in every template.
Без цього треба передавати в кожному view — порушення DRY.

Детальна документація: ADVANCED_TEMPLATES.md §1
"""
from django.contrib.auth.models import Group
from django.db import OperationalError
from django.db.models import Q
from .selectors import get_user_notebooks, get_user_tags
from .models import TodoList, ShoppingList


def sidebar_context(request):
    """Notebooks, tags, todo/shopping counts — injected into every template context."""
    if not request.user.is_authenticated:
        return {
            'sidebar_notebooks': [],
            'sidebar_tags': [],
            'sidebar_todo_count': 0,
            'sidebar_shopping_count': 0,
            'sidebar_groups': [],
        }

    user = request.user
    try:
        todo_count = TodoList.objects.filter(
            Q(user=user) | Q(shared_with=user), is_completed=False
        ).distinct().count()
        shopping_count = ShoppingList.objects.filter(
            Q(user=user) | Q(shared_with=user)
        ).distinct().count()
        sidebar_groups = list(user.groups.all())
    except OperationalError:
        todo_count = 0
        shopping_count = 0
        sidebar_groups = []

    return {
        'sidebar_notebooks': get_user_notebooks(user),
        'sidebar_tags': get_user_tags(user),
        'sidebar_todo_count': todo_count,
        'sidebar_shopping_count': shopping_count,
        'sidebar_groups': sidebar_groups,
    }
