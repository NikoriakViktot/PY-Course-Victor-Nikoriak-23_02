"""
selectors.py — SELECT queries only (no mutations).

Скопійовано з notes_project. Детальна документація ORM оптимізацій:
lesson_Django_ORM_Database/notes_project/hello_app/selectors.py

Auth lesson additions:
  - get_user_notes: includes group notes (Q filter)
  - get_user_shopping_lists: includes group lists
  - get_user_groups, get_group_members: group management selectors
"""
from django.contrib.auth.models import Group
from django.db.models import Count, Q, Prefetch
from django.utils import timezone

from .models import Note, Notebook, Tag, TodoList, TodoItem, ShoppingList, Reminder


def get_user_notes(user, *, archived=False, notebook=None, tag=None, search=None):
    user_groups = user.groups.all()
    qs = Note.objects.filter(
        Q(user=user) | Q(group__in=user_groups), is_archived=archived
    ).select_related('notebook', 'group').prefetch_related('tags')

    if notebook is not None:
        qs = qs.filter(notebook=notebook)
    if tag is not None:
        qs = qs.filter(tags=tag)
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))

    return qs.order_by('-is_pinned', '-priority', '-updated_at')


def get_note_detail(user, note_id):
    user_groups = user.groups.all()
    return Note.objects.filter(
        Q(user=user) | Q(group__in=user_groups)
    ).select_related(
        'notebook', 'user'
    ).prefetch_related(
        'tags',
        Prefetch(
            'reminders',
            queryset=Reminder.objects.filter(
                remind_at__gte=timezone.now()
            ).order_by('remind_at'),
            to_attr='upcoming_reminders'
        )
    ).get(id=note_id)


def get_pinned_notes(user, limit=5):
    return Note.objects.filter(
        user=user, is_pinned=True, is_archived=False
    ).select_related('notebook').prefetch_related('tags')[:limit]


def get_user_notebooks(user):
    return Notebook.objects.filter(user=user).annotate(
        note_count=Count('notes', filter=Q(notes__is_archived=False))
    ).order_by('-is_default', 'title')


def get_user_tags(user):
    return Tag.objects.filter(user=user).annotate(
        note_count=Count('notes', filter=Q(notes__is_archived=False))
    ).order_by('name')


def get_user_todo_lists(user):
    return TodoList.objects.filter(user=user).annotate(
        total_items=Count('items'),
        done_items=Count('items', filter=Q(items__is_done=True))
    ).order_by('is_completed', '-created_at')


def get_shared_todo_lists(user):
    return TodoList.objects.filter(shared_with=user).annotate(
        total_items=Count('items'),
        done_items=Count('items', filter=Q(items__is_done=True))
    ).select_related('user').order_by('is_completed', '-created_at')


def get_todo_list_detail(user, pk):
    try:
        return TodoList.objects.prefetch_related(
            'items', 'shared_with'
        ).get(Q(user=user) | Q(shared_with=user), pk=pk)
    except TodoList.DoesNotExist:
        return None


def get_user_shopping_lists(user):
    user_groups = user.groups.all()
    return ShoppingList.objects.filter(
        Q(user=user) | Q(group__in=user_groups)
    ).distinct().annotate(
        total_items=Count('items'),
        pending_items=Count('items', filter=Q(items__is_purchased=False))
    ).select_related('group').order_by('-created_at')


def get_shared_shopping_lists(user):
    return ShoppingList.objects.filter(shared_with=user).annotate(
        total_items=Count('items'),
        pending_items=Count('items', filter=Q(items__is_purchased=False))
    ).select_related('user').order_by('-created_at')


def get_shopping_list_detail(user, pk):
    try:
        return ShoppingList.objects.prefetch_related(
            'items', 'shared_with'
        ).get(Q(user=user) | Q(shared_with=user), pk=pk)
    except ShoppingList.DoesNotExist:
        return None


def get_pending_reminders():
    return Reminder.objects.filter(
        is_sent=False, remind_at__lte=timezone.now()
    ).select_related('note__user')


# ── Group selectors ───────────────────────────────────────────────────────────

def get_user_groups(user):
    """Groups the user belongs to, annotated with member count."""
    return user.groups.annotate(
        member_count=Count('user')
    ).order_by('name')


def get_group_with_members(group_id, user):
    """Returns group if user is a member, else None."""
    try:
        group = Group.objects.prefetch_related('user_set').get(pk=group_id)
        if not group.user_set.filter(pk=user.pk).exists():
            return None
        return group
    except Group.DoesNotExist:
        return None
