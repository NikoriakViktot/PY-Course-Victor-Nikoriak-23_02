"""
views.py — HTTP шар (тільки request/response).

Тонкі view функції — вся логіка делегована selectors/services.
Деталі архітектурних патернів: lesson_Django_ORM_Database/notes_project/notes_app/views.py
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from .models import Note, Tag, Notebook, TodoList, TodoItem, ShoppingList, ShopItem, Reminder
from .forms import (
    NoteForm, NotebookForm, TagForm,
    TodoListForm, TodoItemForm, ShoppingListForm, ShopItemForm,
    ReminderForm, ShareForm, GroupCreateForm, GroupAddMemberForm,
)
from . import selectors, services


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC VIEWS
# ─────────────────────────────────────────────────────────────────────────────

def index(request):
    if request.user.is_authenticated:
        return redirect('notes_app:note_list')
    return render(request, 'notes_app/index.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('notes_app:note_list')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'✅ Акаунт «{user.username}» створено!')
            return redirect('notes_app:note_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


# ─────────────────────────────────────────────────────────────────────────────
# NOTE VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def note_list(request):
    search = request.GET.get('q', '').strip()
    tag_id = request.GET.get('tag')
    notebook_id = request.GET.get('notebook')

    tag = None
    if tag_id:
        try:
            tag = Tag.objects.get(id=int(tag_id), user=request.user)
        except (Tag.DoesNotExist, ValueError):
            pass

    notebook = None
    if notebook_id:
        try:
            notebook = Notebook.objects.get(id=int(notebook_id), user=request.user)
        except (Notebook.DoesNotExist, ValueError):
            pass

    notes = selectors.get_user_notes(
        request.user,
        search=search or None,
        tag=tag,
        notebook=notebook,
    )
    notebooks = selectors.get_user_notebooks(request.user)
    tags = selectors.get_user_tags(request.user)

    return render(request, 'notes_app/note_list.html', {
        'notes': notes,
        'notebooks': notebooks,
        'tags': tags,
        'search': search,
        'active_tag': tag,
        'active_notebook': notebook,
    })


@login_required
def note_detail(request, pk):
    try:
        note = selectors.get_note_detail(request.user, pk)
    except Note.DoesNotExist:
        raise Http404("Нотатку не знайдено")

    from django.urls import reverse
    reminder_form = ReminderForm()
    reminder_form.helper.form_action = reverse('notes_app:reminder_create', args=[pk])

    return render(request, 'notes_app/note_detail.html', {
        'note': note,
        'reminder_form': reminder_form,
    })


@login_required
def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST, user=request.user)
        if form.is_valid():
            tags = form.cleaned_data.get('tags')
            tag_ids = [t.id for t in tags] if tags else None
            note = services.create_note(
                user=request.user,
                title=form.cleaned_data['title'],
                content=form.cleaned_data.get('content', ''),
                priority=form.cleaned_data.get('priority', 1),
                notebook=form.cleaned_data.get('notebook'),
                group=form.cleaned_data.get('group'),
                tag_ids=tag_ids,
            )
            messages.success(request, f'✅ Нотатку "{note.title}" створено!')
            return redirect('notes_app:note_detail', pk=note.pk)
    else:
        form = NoteForm(user=request.user)

    return render(request, 'notes_app/note_form.html', {
        'form': form,
        'title': 'Нова нотатка',
        'action': 'Створити',
    })


@login_required
def note_edit(request, pk):
    user_groups = request.user.groups.all()
    note = get_object_or_404(
        Note.objects.filter(Q(user=request.user) | Q(group__in=user_groups)),
        pk=pk,
    )
    if note.user != request.user:
        messages.error(request, 'Ти не можеш редагувати нотатку іншого користувача.')
        return redirect('notes_app:note_detail', pk=pk)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note, user=request.user)
        if form.is_valid():
            tags = form.cleaned_data.get('tags')
            tag_ids = [t.id for t in tags] if tags else []
            services.update_note(
                note,
                title=form.cleaned_data['title'],
                content=form.cleaned_data.get('content', ''),
                priority=form.cleaned_data.get('priority', note.priority),
                notebook=form.cleaned_data.get('notebook'),
                is_pinned=form.cleaned_data.get('is_pinned', note.is_pinned),
                group=form.cleaned_data.get('group'),
                tag_ids=tag_ids,
            )
            messages.success(request, f'✅ Нотатку "{note.title}" оновлено!')
            return redirect('notes_app:note_detail', pk=note.pk)
    else:
        form = NoteForm(instance=note, user=request.user)

    return render(request, 'notes_app/note_form.html', {
        'form': form,
        'note': note,
        'title': f'Редагувати: {note.title}',
        'action': 'Зберегти зміни',
    })


@login_required
def note_delete(request, pk):
    user_groups = request.user.groups.all()
    note = get_object_or_404(
        Note.objects.filter(Q(user=request.user) | Q(group__in=user_groups)),
        pk=pk,
    )
    if note.user != request.user:
        messages.error(request, 'Ти не можеш видалити нотатку іншого користувача.')
        return redirect('notes_app:note_list')

    if request.method == 'POST':
        title = note.title
        services.delete_note(note)
        messages.warning(request, f'🗑️ Нотатку "{title}" видалено.')
        return redirect('notes_app:note_list')

    return render(request, 'notes_app/note_confirm_delete.html', {'note': note})


# ─────────────────────────────────────────────────────────────────────────────
# NOTEBOOK VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def notebook_list(request):
    notebooks = selectors.get_user_notebooks(request.user)
    return render(request, 'notes_app/notebook_list.html', {'notebooks': notebooks})


@login_required
def notebook_create(request):
    if request.method == 'POST':
        form = NotebookForm(request.POST)
        if form.is_valid():
            notebook = services.create_notebook(
                user=request.user,
                title=form.cleaned_data['title'],
                color=form.cleaned_data.get('color', '#4A90E2'),
                is_default=form.cleaned_data.get('is_default', False),
            )
            if form.cleaned_data.get('description'):
                notebook.description = form.cleaned_data['description']
                notebook.save(update_fields=['description'])
            messages.success(request, f'Записник "{notebook.title}" створено!')
            return redirect('notes_app:notebook_list')
    else:
        form = NotebookForm()

    return render(request, 'notes_app/notebook_form.html', {
        'form': form, 'title': 'Новий записник', 'action': 'Створити'
    })


@login_required
def notebook_edit(request, pk):
    notebook = get_object_or_404(Notebook, pk=pk, user=request.user)

    if request.method == 'POST':
        form = NotebookForm(request.POST, instance=notebook)
        if form.is_valid():
            services.update_notebook(
                notebook,
                title=form.cleaned_data['title'],
                description=form.cleaned_data.get('description', ''),
                color=form.cleaned_data.get('color', '#4A90E2'),
                is_default=form.cleaned_data.get('is_default', False),
            )
            messages.success(request, f'Записник "{notebook.title}" оновлено!')
            return redirect('notes_app:notebook_list')
    else:
        form = NotebookForm(instance=notebook)

    return render(request, 'notes_app/notebook_form.html', {
        'form': form, 'notebook': notebook,
        'title': f'Редагувати: {notebook.title}', 'action': 'Зберегти'
    })


@login_required
def notebook_delete(request, pk):
    notebook = get_object_or_404(Notebook, pk=pk, user=request.user)

    if request.method == 'POST':
        title = notebook.title
        note_count = notebook.notes.count()
        services.delete_notebook(notebook)
        messages.warning(
            request,
            f'Записник "{title}" видалено. {note_count} нотаток стали без записника.'
        )
        return redirect('notes_app:notebook_list')

    return render(request, 'notes_app/notebook_confirm_delete.html', {
        'notebook': notebook, 'note_count': notebook.notes.count()
    })


# ─────────────────────────────────────────────────────────────────────────────
# TAG VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def tag_create(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'notes_app:note_create'

    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag, created = services.create_or_get_tag(
                user=request.user,
                name=form.cleaned_data['name'],
                color=form.cleaned_data.get('color', '#808080'),
            )
            if created:
                messages.success(request, f'✅ Тег "#{tag.name}" створено!')
            else:
                messages.info(request, f'ℹ️ Тег "#{tag.name}" вже існує.')
            return redirect(next_url)
    else:
        initial = {}
        if request.GET.get('name'):
            initial['name'] = request.GET.get('name')
        form = TagForm(initial=initial)

    return render(request, 'notes_app/tag_form.html', {
        'form': form, 'title': 'Новий тег', 'action': 'Створити', 'next': next_url
    })


# ─────────────────────────────────────────────────────────────────────────────
# TODO VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def todo_list_list(request):
    todo_lists = selectors.get_user_todo_lists(request.user)
    shared_lists = selectors.get_shared_todo_lists(request.user)
    return render(request, 'notes_app/todo_list.html', {
        'todo_lists': todo_lists,
        'shared_lists': shared_lists,
    })


@login_required
def todo_list_create(request):
    if request.method == 'POST':
        form = TodoListForm(request.POST)
        if form.is_valid():
            todo = services.create_todo_list(
                user=request.user,
                title=form.cleaned_data['title'],
                description=form.cleaned_data.get('description', ''),
            )
            messages.success(request, f'✅ Список «{todo.title}» створено!')
            return redirect('notes_app:todo_detail', pk=todo.pk)
    else:
        form = TodoListForm()
    return render(request, 'notes_app/todo_form.html', {
        'form': form, 'title': 'Новий список справ', 'action': 'Створити',
    })


@login_required
def todo_list_detail(request, pk):
    todo = selectors.get_todo_list_detail(request.user, pk)
    if todo is None:
        raise Http404
    item_form = TodoItemForm()
    return render(request, 'notes_app/todo_detail.html', {
        'todo': todo,
        'item_form': item_form,
        'is_owner': todo.user == request.user,
    })


@login_required
def todo_list_edit(request, pk):
    todo = get_object_or_404(
        TodoList.objects.filter(Q(user=request.user) | Q(shared_with=request.user)),
        pk=pk,
    )
    if todo.user != request.user:
        messages.error(request, 'Ти не можеш редагувати список іншого користувача.')
        return redirect('notes_app:todo_detail', pk=pk)
    if request.method == 'POST':
        form = TodoListForm(request.POST, instance=todo)
        if form.is_valid():
            services.update_todo_list(
                todo,
                title=form.cleaned_data['title'],
                description=form.cleaned_data.get('description', ''),
            )
            messages.success(request, f'✅ Список «{todo.title}» оновлено!')
            return redirect('notes_app:todo_detail', pk=todo.pk)
    else:
        form = TodoListForm(instance=todo)
    return render(request, 'notes_app/todo_form.html', {
        'form': form, 'todo': todo, 'title': f'Редагувати: {todo.title}', 'action': 'Зберегти',
    })


@login_required
def todo_list_delete(request, pk):
    todo = get_object_or_404(
        TodoList.objects.filter(Q(user=request.user) | Q(shared_with=request.user)),
        pk=pk,
    )
    if todo.user != request.user:
        messages.error(request, 'Ти не можеш видалити список іншого користувача.')
        return redirect('notes_app:todo_list')
    if request.method == 'POST':
        title = todo.title
        services.delete_todo_list(todo)
        messages.warning(request, f'🗑️ Список «{title}» видалено.')
        return redirect('notes_app:todo_list')
    return render(request, 'notes_app/todo_confirm_delete.html', {'todo': todo})


@login_required
def todo_item_add(request, list_pk):
    todo = selectors.get_todo_list_detail(request.user, list_pk)
    if todo is None:
        raise Http404
    if request.method == 'POST':
        form = TodoItemForm(request.POST)
        if form.is_valid():
            services.add_todo_item(
                todo,
                text=form.cleaned_data['text'],
                due_date=form.cleaned_data.get('due_date'),
            )
    return redirect('notes_app:todo_detail', pk=list_pk)


@login_required
def todo_item_toggle(request, pk):
    item = get_object_or_404(TodoItem, pk=pk)
    todo = item.todo_list
    if todo.user != request.user and not todo.shared_with.filter(pk=request.user.pk).exists():
        raise Http404
    if request.method == 'POST':
        services.toggle_todo_item(item)
    return redirect('notes_app:todo_detail', pk=todo.pk)


@login_required
def todo_item_delete(request, pk):
    item = get_object_or_404(TodoItem, pk=pk, todo_list__user=request.user)
    list_pk = item.todo_list_id
    if request.method == 'POST':
        services.delete_todo_item(item)
    return redirect('notes_app:todo_detail', pk=list_pk)


@login_required
def todo_list_share(request, pk):
    todo = get_object_or_404(TodoList, pk=pk, user=request.user)
    error = None
    if request.method == 'POST':
        form = ShareForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            if request.POST.get('action') == 'remove':
                services.unshare_todo_list(todo, username)
                messages.success(request, f'Доступ для «{username}» скасовано.')
            else:
                ok, msg = services.share_todo_list(todo, username)
                if ok:
                    messages.success(request, f'✅ Список поділено з «{username}».')
                else:
                    error = msg
    else:
        form = ShareForm()
    return render(request, 'notes_app/share_form.html', {
        'form': form, 'obj': todo, 'obj_type': 'todo',
        'shared_with': todo.shared_with.all(), 'error': error,
    })


# ─────────────────────────────────────────────────────────────────────────────
# SHOPPING VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def shopping_list_list(request):
    shopping_lists = selectors.get_user_shopping_lists(request.user)
    shared_lists = selectors.get_shared_shopping_lists(request.user)
    return render(request, 'notes_app/shopping_list.html', {
        'shopping_lists': shopping_lists,
        'shared_lists': shared_lists,
    })


@login_required
def shopping_list_create(request):
    if request.method == 'POST':
        form = ShoppingListForm(request.POST, user=request.user)
        if form.is_valid():
            sl = services.create_shopping_list(
                user=request.user,
                title=form.cleaned_data['title'],
                store_name=form.cleaned_data.get('store_name', ''),
                group=form.cleaned_data.get('group'),
            )
            messages.success(request, f'✅ Список покупок «{sl.title}» створено!')
            return redirect('notes_app:shopping_detail', pk=sl.pk)
    else:
        form = ShoppingListForm(user=request.user)
    return render(request, 'notes_app/shopping_form.html', {
        'form': form, 'title': 'Новий список покупок', 'action': 'Створити',
    })


@login_required
def shopping_list_detail(request, pk):
    sl = selectors.get_shopping_list_detail(request.user, pk)
    if sl is None:
        raise Http404
    item_form = ShopItemForm()
    total_price = sum(
        (i.estimated_price or 0) * i.quantity
        for i in sl.items.all()
        if not i.is_purchased
    )
    return render(request, 'notes_app/shopping_detail.html', {
        'sl': sl,
        'item_form': item_form,
        'total_price': total_price,
        'is_owner': sl.user == request.user,
    })


@login_required
def shopping_list_edit(request, pk):
    sl = get_object_or_404(
        ShoppingList.objects.filter(Q(user=request.user) | Q(shared_with=request.user)),
        pk=pk,
    )
    if sl.user != request.user:
        messages.error(request, 'Ти не можеш редагувати список іншого користувача.')
        return redirect('notes_app:shopping_detail', pk=pk)
    if request.method == 'POST':
        form = ShoppingListForm(request.POST, instance=sl, user=request.user)
        if form.is_valid():
            services.update_shopping_list(
                sl,
                title=form.cleaned_data['title'],
                store_name=form.cleaned_data.get('store_name', ''),
                group=form.cleaned_data.get('group'),
            )
            messages.success(request, f'✅ Список «{sl.title}» оновлено!')
            return redirect('notes_app:shopping_detail', pk=sl.pk)
    else:
        form = ShoppingListForm(instance=sl, user=request.user)
    return render(request, 'notes_app/shopping_form.html', {
        'form': form, 'sl': sl, 'title': f'Редагувати: {sl.title}', 'action': 'Зберегти',
    })


@login_required
def shopping_list_delete(request, pk):
    sl = get_object_or_404(
        ShoppingList.objects.filter(Q(user=request.user) | Q(shared_with=request.user)),
        pk=pk,
    )
    if sl.user != request.user:
        messages.error(request, 'Ти не можеш видалити список іншого користувача.')
        return redirect('notes_app:shopping_list')
    if request.method == 'POST':
        title = sl.title
        services.delete_shopping_list(sl)
        messages.warning(request, f'🗑️ Список «{title}» видалено.')
        return redirect('notes_app:shopping_list')
    return render(request, 'notes_app/shopping_confirm_delete.html', {'sl': sl})


@login_required
def shop_item_add(request, list_pk):
    sl = selectors.get_shopping_list_detail(request.user, list_pk)
    if sl is None:
        raise Http404
    if request.method == 'POST':
        form = ShopItemForm(request.POST)
        if form.is_valid():
            services.add_shop_item(
                sl,
                name=form.cleaned_data['name'],
                quantity=form.cleaned_data.get('quantity', 1),
                unit=form.cleaned_data.get('unit', 'шт'),
                estimated_price=form.cleaned_data.get('estimated_price'),
            )
    return redirect('notes_app:shopping_detail', pk=list_pk)


@login_required
def shop_item_toggle(request, pk):
    item = get_object_or_404(ShopItem, pk=pk)
    sl = item.shopping_list
    if sl.user != request.user and not sl.shared_with.filter(pk=request.user.pk).exists():
        raise Http404
    if request.method == 'POST':
        services.toggle_shop_item_purchased(item)
    return redirect('notes_app:shopping_detail', pk=sl.pk)


@login_required
def shop_item_delete(request, pk):
    item = get_object_or_404(ShopItem, pk=pk, shopping_list__user=request.user)
    list_pk = item.shopping_list_id
    if request.method == 'POST':
        services.delete_shop_item(item)
    return redirect('notes_app:shopping_detail', pk=list_pk)


@login_required
def shopping_list_share(request, pk):
    sl = get_object_or_404(ShoppingList, pk=pk, user=request.user)
    error = None
    if request.method == 'POST':
        form = ShareForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            if request.POST.get('action') == 'remove':
                services.unshare_shopping_list(sl, username)
                messages.success(request, f'Доступ для «{username}» скасовано.')
            else:
                ok, msg = services.share_shopping_list(sl, username)
                if ok:
                    messages.success(request, f'✅ Список поділено з «{username}».')
                else:
                    error = msg
    else:
        form = ShareForm()
    return render(request, 'notes_app/share_form.html', {
        'form': form, 'obj': sl, 'obj_type': 'shopping',
        'shared_with': sl.shared_with.all(), 'error': error,
    })


# ─────────────────────────────────────────────────────────────────────────────
# REMINDER VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def reminder_create(request, note_pk):
    note = get_object_or_404(Note, pk=note_pk, user=request.user)
    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            services.create_reminder(
                note=note,
                remind_at=form.cleaned_data['remind_at'],
                message=form.cleaned_data.get('message', ''),
                repeat_pattern=form.cleaned_data.get('repeat_pattern', 'none'),
            )
            messages.success(request, '✅ Нагадування додано!')
    return redirect('notes_app:note_detail', pk=note_pk)


@login_required
def reminder_delete(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, note__user=request.user)
    note_pk = reminder.note_id
    if request.method == 'POST':
        services.delete_reminder(reminder)
        messages.warning(request, '🗑️ Нагадування видалено.')
    return redirect('notes_app:note_detail', pk=note_pk)


# ─────────────────────────────────────────────────────────────────────────────
# GROUP VIEWS — Django built-in Group model
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def group_list(request):
    groups = selectors.get_user_groups(request.user)
    return render(request, 'notes_app/group_list.html', {'groups': groups})


@login_required
def group_create(request):
    if request.method == 'POST':
        form = GroupCreateForm(request.POST)
        if form.is_valid():
            group = services.create_group(
                name=form.cleaned_data['name'],
                creator=request.user,
            )
            messages.success(request, f'✅ Групу «{group.name}» створено! Ви перший учасник.')
            return redirect('notes_app:group_detail', pk=group.pk)
    else:
        form = GroupCreateForm()
    return render(request, 'notes_app/group_form.html', {
        'form': form, 'title': 'Нова група', 'action': 'Створити',
    })


@login_required
def group_detail(request, pk):
    group = selectors.get_group_with_members(pk, request.user)
    if group is None:
        raise Http404('Групу не знайдено або у вас немає доступу.')

    add_form = GroupAddMemberForm()
    error = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            add_form = GroupAddMemberForm(request.POST)
            if add_form.is_valid():
                ok, msg = services.add_user_to_group(group, add_form.cleaned_data['username'])
                if ok:
                    messages.success(request, f'✅ Користувача додано до групи.')
                    return redirect('notes_app:group_detail', pk=pk)
                else:
                    error = msg
        elif action == 'remove':
            from django.contrib.auth.models import User as AuthUser
            remove_pk = request.POST.get('user_pk')
            try:
                target = AuthUser.objects.get(pk=remove_pk)
                if target == request.user:
                    messages.warning(request, 'Вийти з групи можна через кнопку «Покинути групу».')
                else:
                    services.remove_user_from_group(group, target)
                    messages.success(request, f'Користувача «{target.username}» видалено з групи.')
            except AuthUser.DoesNotExist:
                pass
            return redirect('notes_app:group_detail', pk=pk)
        elif action == 'leave':
            services.remove_user_from_group(group, request.user)
            messages.info(request, f'Ви покинули групу «{group.name}».')
            return redirect('notes_app:group_list')

    return render(request, 'notes_app/group_detail.html', {
        'group': group,
        'members': group.user_set.all(),
        'add_form': add_form,
        'error': error,
    })


@login_required
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if not group.user_set.filter(pk=request.user.pk).exists():
        raise PermissionDenied
    if request.method == 'POST':
        name = group.name
        services.delete_group(group)
        messages.warning(request, f'Групу «{name}» видалено.')
        return redirect('notes_app:group_list')
    return render(request, 'notes_app/group_confirm_delete.html', {'group': group})


@login_required
def group_chat(request, pk):
    """
    HTTP GET → рендерить сторінку групового чату.

    НАВЧАЛЬНА РОЛЬ ЦІЄї VIEW:
    ──────────────────────────
    Ця view робить ОДНЕ: перевіряє членство і рендерить HTML-сторінку.
    Реальний чат відбувається ПІСЛЯ через WebSocket (consumers.py).

    Два кроки:
        1. GET /groups/7/chat/     → ця view → group_chat.html (HTML + JS)
        2. JS відкриває            → ws://host/ws/groups/7/chat/ → GroupChatConsumer

    Чому не можна все зробити через WebSocket?
    ──────────────────────────────────────────
    WebSocket не може рендерити HTML-сторінку.
    Браузер спочатку завантажує HTML через звичайний HTTP,
    а потім цей HTML містить JS код який відкриває WebSocket.
    Це стандартна практика: HTTP для сторінки, WS для даних.
    """
    group = get_object_or_404(Group, pk=pk)
    if not group.user_set.filter(pk=request.user.pk).exists():
        messages.error(request, 'Ти не є членом цієї групи.')
        return redirect('notes_app:group_list')
    return render(request, 'notes_app/group_chat.html', {'group': group})
