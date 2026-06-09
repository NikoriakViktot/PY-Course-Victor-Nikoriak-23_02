"""
async_views.py — async def views для Notes.

Навчальна ідея:
───────────────
Цей файл є async-версією views.py (тільки для Notes).
Порівнюй кожну функцію з її sync-аналогом у views.py.

URL-и для порівняння:
    Sync:  http://127.0.0.1:8000/notes/              → views.note_list
    Async: http://127.0.0.1:8001/async/notes/        → async_views.async_note_list

    Sync:  http://127.0.0.1:8000/notes/<id>/         → views.note_detail
    Async: http://127.0.0.1:8001/async/notes/<id>/   → async_views.async_note_detail

    і так далі для create, delete, toggle_pin.

Що змінилось у async views?
────────────────────────────
    1. async def замість def
    2. ORM-операції через async_selectors і async_services
    3. async for замість for при ітерації по QuerySet
    4. await перед кожним зверненням до БД
    5. Auth check inline (замість @login_required) — для навчальної прозорості
    6. await request.auser() замість request.user — ось чому:

КРИТИЧНО: request.user vs await request.auser()
────────────────────────────────────────────────
    request.user → SimpleLazyObject(lambda: get_user(request))
                   При доступі викликає SYNC get_user() →
                   SYNC User.objects.get(pk=user_id) →
                   SynchronousOnlyOperation в async view!

    await request.auser() → Django 4.2+ async API →
                            ASYNC aget_user() →
                            ASYNC User.objects.aget(pk=user_id) →
                            Безпечно в async view ✅

    Правило: в async def view ЗАВЖДИ використовуй await request.auser().

Що НЕ змінилось?
─────────────────
    - redirect() — безпечно викликати з async def
    - messages.success/error/warning() — безпечно
    - Логіка — однакова з sync views
    - Templates — ті самі що й sync views (переважно)

ВАЖЛИВО: render() та context processors з sync ORM:
────────────────────────────────────────────────────
    render() сама по собі не є проблемою.
    АЛЕ: контекстні процесори (context_processors.py → sidebar_context)
    роблять sync ORM-запити (TodoList.objects.filter(...).count()).
    Якщо render() викликати напряму з async view, ці ORM-запити
    виконуються у async event loop і кидають SynchronousOnlyOperation.

    Рішення: await sync_to_async(render)(request, template, context)
    → render() виконується у worker thread → sync ORM безпечний.

    Це стосується БУДЬ-ЯКИХ sync операцій під час рендерингу шаблону.

Про @login_required у async views:
────────────────────────────────────
    У Django 5.x @login_required повністю підтримує async views.
    Але в цьому навчальному файлі ми робимо auth-перевірку ЯВНО всередині,
    щоб студент бачив де і як це відбувається.
    Це педагогічний вибір, не технічна необхідність.

Документація:
    Django async views: https://docs.djangoproject.com/en/5.2/topics/async/
    Async ORM: https://docs.djangoproject.com/en/5.2/ref/models/querysets/#async-queries
    request.auser(): https://docs.djangoproject.com/en/5.2/ref/request-response/#django.http.HttpRequest.auser
"""
from asgiref.sync import sync_to_async
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from django.urls import reverse

from .models import Note, Tag, Notebook
from .forms import NoteForm, ReminderForm
from . import async_selectors, async_services


# ─────────────────────────────────────────────────────────────────────────────
# NOTE LIST
# ─────────────────────────────────────────────────────────────────────────────

async def async_note_list(request):
    """
    Список нотаток поточного користувача.

    Sync-аналог: views.note_list() — views.py:56
    URL: GET /async/notes/

    КЛЮЧОВІ ВІДМІННОСТІ від sync версії:
    ──────────────────────────────────────
    1. await request.auser() — async-safe отримання user (не request.user!)
    2. async_get_user_notes() повертає LAZY QuerySet (SQL ще не виконаний)
    3. async for — тут відбувається реальне async звернення до БД
    4. Event loop вільний поки DB виконує SELECT
    """
    # ── Auth check ──────────────────────────────────────────────────────────
    # await request.auser() — Django 4.2+ async API для отримання user.
    # НЕ request.user — він lazy і викликає SYNC User.objects.get() всередині!
    user = await request.auser()
    # Кешуємо user для sync-коду (context processors, шаблони).
    # get_user() перевіряє _cached_user першим — DB-запиту не буде.
    request._cached_user = user
    if not user.is_authenticated:
        # redirect('login') → /accounts/login/?next=/async/notes/
        return redirect('login')

    # ── Параметри фільтрації з URL ──────────────────────────────────────────
    search = request.GET.get('q', '').strip()
    tag_id = request.GET.get('tag')
    notebook_id = request.GET.get('notebook')

    # Отримати конкретний тег для фільтру (якщо є в URL)
    tag = None
    if tag_id:
        try:
            # await aget() — реальний async SQL, звільняє event loop під час очікування
            tag = await Tag.objects.aget(id=int(tag_id), user=user)
        except (Tag.DoesNotExist, ValueError):
            pass  # невалідний id або не наш тег — ігноруємо

    # Отримати конкретний записник для фільтру
    notebook = None
    if notebook_id:
        try:
            notebook = await Notebook.objects.aget(id=int(notebook_id), user=user)
        except (Notebook.DoesNotExist, ValueError):
            pass

    # ── ORM: Lazy QuerySet ──────────────────────────────────────────────────
    # async_get_user_notes() — НЕ йде до БД! Повертає lazy QuerySet.
    # Всі .filter(), .select_related(), .prefetch_related() — lazy.
    # SQL ще не виконується.
    notes_qs = async_selectors.async_get_user_notes(
        user,
        search=search or None,
        tag=tag,
        notebook=notebook,
    )

    # ── async for — ТУТ виконується SQL ────────────────────────────────────
    # Event loop призупиняє цю coroutine і обслуговує інші запити поки DB
    # виконує SELECT ... JOIN ... WHERE ...
    # Результат: notes — звичайний Python list
    notes = [note async for note in notes_qs]

    # Аналогічно для notebooks і tags — lazy QuerySet → async for → list
    notebooks = [nb async for nb in async_selectors.async_get_user_notebooks(user)]
    all_tags = [t async for t in async_selectors.async_get_user_tags(user)]

    # render() — sync, але безпечна у async def view (Django 5.x)
    # Шаблон той самий що й sync view — HTML не треба змінювати
    return await sync_to_async(render)(request, 'notes_app/note_list.html', {
        'notes': notes,
        'notebooks': notebooks,
        'tags': all_tags,
        'search': search,
        'active_tag': tag,
        'active_notebook': notebook,
    })


# ─────────────────────────────────────────────────────────────────────────────
# NOTE DETAIL
# ─────────────────────────────────────────────────────────────────────────────

async def async_note_detail(request, pk):
    """
    Деталі однієї нотатки.

    Sync-аналог: views.note_detail() — views.py:95
    URL: GET /async/notes/<pk>/

    КЛЮЧОВІ ВІДМІННОСТІ:
    ──────────────────────
    1. await request.auser() — async-safe отримання user
    2. await async_get_note_detail() — реальний async SQL (aget всередині)
    3. try/except Note.DoesNotExist — той самий механізм що й у sync версії
    """
    user = await request.auser()
    request._cached_user = user  # кеш для sync context processors/templates
    if not user.is_authenticated:
        return redirect('login')

    try:
        # await: coroutine призупиняється тут, DB виконує SELECT з JOIN та prefetch.
        # async_get_note_detail() всередині використовує .aget() — async SQL.
        # Якщо нотатку не знайдено або вона не belongs to user → Note.DoesNotExist
        note = await async_selectors.async_get_note_detail(user, pk)
    except Note.DoesNotExist:
        raise Http404("Нотатку не знайдено")

    reminder_form = ReminderForm()
    reminder_form.helper.form_action = reverse('notes_app:reminder_create', args=[pk])

    return await sync_to_async(render)(request, 'notes_app/note_detail.html', {
        'note': note,
        'reminder_form': reminder_form,
    })


# ─────────────────────────────────────────────────────────────────────────────
# NOTE CREATE
# ─────────────────────────────────────────────────────────────────────────────

async def async_note_create(request):
    """
    Форма створення нотатки.

    Sync-аналог: views.note_create() — views.py:112
    URL: GET/POST /async/notes/create/

    КЛЮЧОВІ ВІДМІННОСТІ:
    ──────────────────────
    1. await request.auser() — async-safe отримання user
    2. NoteForm(request.POST, user=user) — sync (форма не робить важкий I/O)
    3. form.is_valid() — sync (валідація полів без мережевих операцій)
    4. await async_create_note(...) — async через sync_to_async (там transaction.atomic)

    ЧОМУ форма залишається sync?
    ────────────────────────────
    NoteForm.is_valid() перевіряє типи, довжину рядків, required-поля.
    Це CPU-операції без I/O — async не додає переваги.

    NoteForm.__init__ виконує:
        self.fields['notebook'].queryset = Notebook.objects.filter(user=user)
    Ці QuerySets — lazy, SQL виконає Django при рендерингу форми у шаблоні.

    У production async-коді: можна обернути form.is_valid() у sync_to_async,
    але для навчального проєкту — це зайва складність.
    """
    user = await request.auser()
    request._cached_user = user  # кеш для sync context processors/templates
    if not user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        form = NoteForm(request.POST, user=user)

        # form.is_valid() → validate_constraints() → sync ORM (UniqueConstraint check)
        # Потрібен sync_to_async щоб валідація виконалась у worker thread.
        if await sync_to_async(form.is_valid)():
            tags = form.cleaned_data.get('tags')
            tag_ids = [t.id for t in tags] if tags else None

            # await async_create_note() — ось де async!
            # async_create_note = sync_to_async(create_note, thread_sensitive=True)
            # Всередині: transaction.atomic() + Note.objects.create() + tags.set()
            # sync_to_async запускає це у виділеному sync потоці, event loop вільний.
            note = await async_services.async_create_note(
                user=user,
                title=form.cleaned_data['title'],
                content=form.cleaned_data.get('content', ''),
                priority=form.cleaned_data.get('priority', 1),
                notebook=form.cleaned_data.get('notebook'),
                group=form.cleaned_data.get('group'),
                tag_ids=tag_ids,
            )

            messages.success(request, f'✅ Нотатку "{note.title}" створено (async view)!')
            # redirect() — sync, безпечна у async def view
            return redirect('notes_app:async_note_detail', pk=note.pk)
    else:
        form = NoteForm(user=user)

    return await sync_to_async(render)(request, 'notes_app/note_form.html', {
        'form': form,
        'title': 'Нова нотатка (async)',
        'action': 'Створити',
    })


# ─────────────────────────────────────────────────────────────────────────────
# NOTE DELETE
# ─────────────────────────────────────────────────────────────────────────────

async def async_note_delete(request, pk):
    """
    Підтвердження та видалення нотатки.

    Sync-аналог: views.note_delete() — views.py:179
    URL: GET/POST /async/notes/<pk>/delete/

    КЛЮЧОВІ ВІДМІННОСТІ:
    ──────────────────────
    1. await request.auser() — async-safe отримання user
    2. await async_get_note_detail() — async SQL для завантаження об'єкта
    3. await async_delete_note(note) — async SQL DELETE через .adelete()
    """
    user = await request.auser()
    request._cached_user = user  # кеш для sync context processors/templates
    if not user.is_authenticated:
        return redirect('login')

    try:
        # await: перевіряємо що нотатка існує і belongs to user (або його групу)
        note = await async_selectors.async_get_note_detail(user, pk)
    except Note.DoesNotExist:
        raise Http404("Нотатку не знайдено")

    # Тільки власник може видалити (не member групи)
    if note.user != user:
        messages.error(request, 'Ти не можеш видалити нотатку іншого користувача.')
        return redirect('notes_app:async_note_list')

    if request.method == 'POST':
        title = note.title
        # await async_delete_note() — всередині note.adelete() — async SQL DELETE
        # Event loop вільний поки DB виконує DELETE
        await async_services.async_delete_note(note)
        messages.warning(request, f'🗑️ Нотатку "{title}" видалено (async).')
        return redirect('notes_app:async_note_list')

    # GET → сторінка підтвердження (той самий шаблон що й sync)
    return await sync_to_async(render)(request, 'notes_app/note_confirm_delete.html', {'note': note})


# ─────────────────────────────────────────────────────────────────────────────
# NOTE TOGGLE PIN
# ─────────────────────────────────────────────────────────────────────────────

async def async_note_toggle_pin(request, pk):
    """
    Перемикає is_pinned нотатки (закріпити / відкріпити).

    Sync-аналог: немає як окремого URL у sync views.py.
    Sync-версія змінює is_pinned через note_edit (форму).
    Ми додаємо це як окремий async endpoint для демонстрації aupdate() + F().

    URL: POST /async/notes/<pk>/pin/

    КЛЮЧОВІ ВІДМІННОСТІ:
    ──────────────────────
    1. await request.auser() — async-safe отримання user
    2. await async_get_note_detail() — завантаження об'єкта
    3. await async_toggle_pin_note() — всередині:
         await Note.objects.filter(pk=note.pk).aupdate(is_pinned=~F('is_pinned'))
       Це атомарний SQL UPDATE без завантаження об'єкта у Python.
    """
    user = await request.auser()
    request._cached_user = user  # кеш для sync context processors/templates
    if not user.is_authenticated:
        return redirect('login')

    try:
        note = await async_selectors.async_get_note_detail(user, pk)
    except Note.DoesNotExist:
        raise Http404("Нотатку не знайдено")

    if note.user != user:
        messages.error(request, 'Ти не можеш змінити нотатку іншого користувача.')
        return redirect('notes_app:async_note_list')

    if request.method == 'POST':
        # await: aupdate() всередині — atomic SQL UPDATE SET is_pinned = NOT is_pinned
        # F('is_pinned') читає значення з БД (не з Python об'єкту) — race condition safe
        await async_services.async_toggle_pin_note(note)

        # note.is_pinned ще OLD значення (об'єкт не перезавантажено)
        # aupdate не оновлює Python-об'єкт автоматично
        action = "відкріплено" if note.is_pinned else "закріплено"
        messages.success(request, f'📌 Нотатку "{note.title}" {action} (async).')

    return redirect('notes_app:async_note_detail', pk=pk)
