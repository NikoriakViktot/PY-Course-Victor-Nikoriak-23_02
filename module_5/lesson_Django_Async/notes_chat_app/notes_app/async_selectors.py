"""
async_selectors.py — ORM-запити для async views.

Навчальна ідея:
───────────────
Цей файл є async-версією selectors.py.
Порівнюй кожну функцію з її sync-аналогом у selectors.py.

Ключове розуміння: що є lazy, а що реально йде до БД?
─────────────────────────────────────────────────────
  .filter(...)           → lazy  (лише будує SQL-запит, не виконує)
  .select_related(...)   → lazy  (додає JOIN до опису запиту)
  .prefetch_related(...) → lazy  (планує prefetch, не виконує)
  .annotate(...)         → lazy  (додає підзапит до опису)
  .order_by(...)         → lazy  (додає ORDER BY)

  .get()                 → sync SQL  → у async view кине SynchronousOnlyOperation!
  .aget()                → async SQL → правильний спосіб у async view
  .acount()              → async SQL → async аналог .count()
  .afirst()              → async SQL → async аналог .first()
  async for obj in qs    → async SQL → async аналог for obj in qs

Документація:
  Django async ORM: https://docs.djangoproject.com/en/5.2/topics/db/queries/#async-queries
"""

from django.db.models import Count, Q, Prefetch
from django.utils import timezone

from .models import Note, Notebook, Tag, Reminder


# ─────────────────────────────────────────────────────────────────────────────
# NOTE SELECTORS
# ─────────────────────────────────────────────────────────────────────────────

def async_get_user_notes(user, *, archived=False, notebook=None, tag=None, search=None):
    """
    Повертає lazy QuerySet нотаток для async-ітерації у view.

    Sync-аналог: selectors.get_user_notes() — структура ідентична.

    ЧОМУ ЦЯ ФУНКЦІЯ НЕ async def?
    ──────────────────────────────
    Бо вона нічого не робить з базою даних!
    Вона лише БУДУЄ опис запиту (QuerySet AST).
    Реальний SQL-запит виконується ПІЗНІШЕ — коли view робить:
        async for note in queryset:   ← ось тут SQL
    або
        await queryset.aget(...)      ← ось тут SQL

    Якщо б ми зробили функцію async def, нам довелось би ставити await,
    а отже — виконувати SQL одразу. Але нам треба повернути QuerySet
    для того щоб view міг додати фільтри або ітеруватись по ньому.
    """
    # user.groups.all() — lazy, безпечно
    user_groups = user.groups.all()

    # .filter() — лише будує умову WHERE, SQL не виконується
    qs = Note.objects.filter(
        Q(user=user) | Q(group__in=user_groups),
        is_archived=archived,
    )

    # .select_related() — планує JOIN, SQL не виконується
    qs = qs.select_related('notebook', 'group')

    # .prefetch_related() — планує окремий SQL-запит для tags, не виконується зараз
    qs = qs.prefetch_related('tags')

    # Опційні фільтри — все ще lazy
    if notebook is not None:
        qs = qs.filter(notebook=notebook)
    if tag is not None:
        qs = qs.filter(tags=tag)
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))

    # .order_by() — додає ORDER BY до опису, SQL не виконується
    return qs.order_by('-is_pinned', '-priority', '-updated_at')
    # ↑ View отримує цей QuerySet і робить:
    #   async for note in queryset   ← тут Django виконає SQL асинхронно


async def async_get_note_detail(user, note_id):
    """
    Повертає одну нотатку з усіма пов'язаними даними.

    Sync-аналог: selectors.get_note_detail() — однакова логіка.

    ЧОМУ ЦЯ ФУНКЦІЯ async def?
    ───────────────────────────
    Бо вона реально йде до бази даних через .aget()!
    .aget() — це async-аналог .get().

    Порівняй:
      Sync:  Note.objects.get(id=note_id)   → блокує потік до відповіді DB
      Async: await Note.objects.aget(...)   → призупиняє coroutine, event loop вільний

    Якщо нотатку не знайдено — кидає Note.DoesNotExist, як і .get().
    View має обробити цей виняток через try/except.
    """
    user_groups = user.groups.all()

    # Будуємо lazy QuerySet з joins та prefetch (SQL ще не виконується)
    qs = Note.objects.filter(
        Q(user=user) | Q(group__in=user_groups)
    ).select_related(
        'notebook', 'user'
    ).prefetch_related(
        'tags',
        # Prefetch: лише нагадування у майбутньому (оптимізований підзапит)
        Prefetch(
            'reminders',
            queryset=Reminder.objects.filter(
                remind_at__gte=timezone.now()
            ).order_by('remind_at'),
            to_attr='upcoming_reminders',
        )
    )

    # .aget() — ТЕПЕР реально виконує SQL асинхронно.
    # await призупиняє цю coroutine, event loop обслуговує інших.
    # Коли DB відповідає — coroutine продовжується з результатом.
    return await qs.aget(id=note_id)


# ─────────────────────────────────────────────────────────────────────────────
# NOTEBOOK & TAG SELECTORS
# ─────────────────────────────────────────────────────────────────────────────

def async_get_user_notebooks(user):
    """
    Повертає lazy QuerySet записників з кількістю нотаток.

    Sync-аналог: selectors.get_user_notebooks() — ідентичний.

    ЧОМУ НЕ async def?
    ──────────────────
    .annotate(Count(...)) — ще lazy. SQL виконається у view при ітерації.
    Функція просто конфігурує QuerySet, не звертаючись до DB.
    """
    # annotate додає підзапит COUNT до QuerySet — але SQL не виконується
    return Notebook.objects.filter(user=user).annotate(
        note_count=Count('notes', filter=Q(notes__is_archived=False))
    ).order_by('-is_default', 'title')


def async_get_user_tags(user):
    """
    Повертає lazy QuerySet тегів з кількістю нотаток.

    Sync-аналог: selectors.get_user_tags() — ідентичний.
    """
    return Tag.objects.filter(user=user).annotate(
        note_count=Count('notes', filter=Q(notes__is_archived=False))
    ).order_by('name')
