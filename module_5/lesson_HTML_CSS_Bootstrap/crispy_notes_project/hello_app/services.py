"""
services.py — INSERT / UPDATE / DELETE with business logic.

Скопійовано з notes_project. Детальна документація транзакцій:
lesson_Django_ORM_Database/notes_project/hello_app/services.py
"""
from django.db import transaction
from django.db.models import F, Max

from .models import Note, Notebook, Tag, TodoList, TodoItem, ShoppingList, ShopItem, Reminder


def create_note(*, user, title, content='', notebook=None, priority=1, tag_ids=None):
    with transaction.atomic():
        note = Note.objects.create(
            user=user, title=title, content=content, notebook=notebook, priority=priority
        )
        if tag_ids:
            valid_tags = Tag.objects.filter(id__in=tag_ids, user=user)
            note.tags.set(valid_tags)
    return note


def update_note(note, *, title=None, content=None, priority=None,
                notebook=None, is_pinned=None, tag_ids=None):
    changed_fields = []
    if title is not None:
        note.title = title
        changed_fields.append('title')
    if content is not None:
        note.content = content
        changed_fields.append('content')
    if priority is not None:
        note.priority = priority
        changed_fields.append('priority')
    if is_pinned is not None:
        note.is_pinned = is_pinned
        changed_fields.append('is_pinned')
    if notebook is not None:
        note.notebook = notebook
        changed_fields.append('notebook')
    if changed_fields:
        note.save(update_fields=changed_fields)
    if tag_ids is not None:
        valid_tags = Tag.objects.filter(id__in=tag_ids, user=note.user)
        note.tags.set(valid_tags)
    return note


def delete_note(note):
    note.delete()


def toggle_pin_note(note):
    Note.objects.filter(pk=note.pk).update(is_pinned=~F('is_pinned'))
    note.refresh_from_db(fields=['is_pinned'])
    return note


def archive_note(note):
    Note.objects.filter(pk=note.pk).update(is_archived=True)


def create_notebook(*, user, title, color='#4A90E2', is_default=False):
    with transaction.atomic():
        if is_default:
            Notebook.objects.filter(user=user, is_default=True).update(is_default=False)
        return Notebook.objects.create(user=user, title=title, color=color, is_default=is_default)


def update_notebook(notebook, *, title, description='', color, is_default):
    with transaction.atomic():
        if is_default and not notebook.is_default:
            Notebook.objects.filter(
                user=notebook.user, is_default=True
            ).exclude(pk=notebook.pk).update(is_default=False)
        notebook.title = title
        notebook.description = description
        notebook.color = color
        notebook.is_default = is_default
        notebook.save(update_fields=['title', 'description', 'color', 'is_default'])
    return notebook


def delete_notebook(notebook):
    notebook.delete()


def create_or_get_tag(*, user, name, color='#808080'):
    tag, created = Tag.objects.get_or_create(
        user=user,
        name=name.lower().strip(),
        defaults={'color': color}
    )
    return tag, created


# ─── TodoList ────────────────────────────────────────────────────────────────

def create_todo_list(*, user, title, description=''):
    return TodoList.objects.create(user=user, title=title, description=description)


def update_todo_list(todo_list, *, title, description=''):
    todo_list.title = title
    todo_list.description = description
    todo_list.save(update_fields=['title', 'description'])
    return todo_list


def delete_todo_list(todo_list):
    todo_list.delete()


def complete_todo_list(todo_list):
    with transaction.atomic():
        todo_list.items.filter(is_done=False).update(is_done=True)
        todo_list.is_completed = True
        todo_list.save(update_fields=['is_completed'])


def share_todo_list(todo_list, username):
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return False, f'Користувача «{username}» не знайдено.'
    if user == todo_list.user:
        return False, 'Не можна поділитись із собою.'
    todo_list.shared_with.add(user)
    return True, ''


def unshare_todo_list(todo_list, username):
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(username=username)
        todo_list.shared_with.remove(user)
    except User.DoesNotExist:
        pass


# ─── TodoItem ────────────────────────────────────────────────────────────────

def add_todo_item(todo_list, *, text, due_date=None):
    max_pos = todo_list.items.aggregate(m=Max('order_position'))['m'] or 0
    return TodoItem.objects.create(
        todo_list=todo_list,
        text=text,
        due_date=due_date,
        order_position=max_pos + 1,
    )


def toggle_todo_item(item):
    TodoItem.objects.filter(pk=item.pk).update(is_done=~F('is_done'))
    item.refresh_from_db(fields=['is_done'])
    return item


def delete_todo_item(item):
    item.delete()


# ─── ShoppingList ─────────────────────────────────────────────────────────────

def create_shopping_list(*, user, title, store_name=''):
    return ShoppingList.objects.create(user=user, title=title, store_name=store_name)


def update_shopping_list(shopping_list, *, title, store_name=''):
    shopping_list.title = title
    shopping_list.store_name = store_name
    shopping_list.save(update_fields=['title', 'store_name'])
    return shopping_list


def delete_shopping_list(shopping_list):
    shopping_list.delete()


def share_shopping_list(shopping_list, username):
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return False, f'Користувача «{username}» не знайдено.'
    if user == shopping_list.user:
        return False, 'Не можна поділитись із собою.'
    shopping_list.shared_with.add(user)
    return True, ''


def unshare_shopping_list(shopping_list, username):
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(username=username)
        shopping_list.shared_with.remove(user)
    except User.DoesNotExist:
        pass


# ─── ShopItem ────────────────────────────────────────────────────────────────

def add_shop_item(shopping_list, *, name, quantity=1, unit='шт', estimated_price=None):
    return ShopItem.objects.create(
        shopping_list=shopping_list,
        name=name,
        quantity=quantity,
        unit=unit,
        estimated_price=estimated_price,
    )


def toggle_shop_item_purchased(item):
    ShopItem.objects.filter(pk=item.pk).update(is_purchased=~F('is_purchased'))
    item.refresh_from_db(fields=['is_purchased'])
    return item


def delete_shop_item(item):
    item.delete()


# ─── Reminder ────────────────────────────────────────────────────────────────

def create_reminder(*, note, remind_at, message='', repeat_pattern='none'):
    return Reminder.objects.create(
        note=note,
        remind_at=remind_at,
        message=message,
        repeat_pattern=repeat_pattern,
    )


def delete_reminder(reminder):
    reminder.delete()
