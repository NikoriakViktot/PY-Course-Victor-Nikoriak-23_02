"""
async_services.py — async-обгортки для бізнес-логіки Notes.

Навчальна ідея:
───────────────
Цей файл показує два різних підходи до async business operations:

  1. sync_to_async()  — для операцій із transaction.atomic() або складною sync-логікою
  2. Native async ORM — для простих операцій (adelete, aupdate, asave)

Sync-аналог: services.py — оригінальні функції залишаються незмінними.
Ми не замінюємо sync — ми додаємо async-варіанти поруч.

Документація:
  sync_to_async: https://docs.djangoproject.com/en/5.2/topics/async/#asgiref-sync
  adelete:       https://docs.djangoproject.com/en/5.2/ref/models/instances/#django.db.models.Model.adelete
  aupdate:       https://docs.djangoproject.com/en/5.2/ref/models/querysets/#aupdate
"""

from asgiref.sync import sync_to_async
from django.db.models import F

from .models import Note
from .services import create_note  # Імпортуємо оригінальну sync функцію


# ─────────────────────────────────────────────────────────────────────────────
# CREATE — через sync_to_async (бо є transaction.atomic)
# ─────────────────────────────────────────────────────────────────────────────

# async_create_note = sync_to_async(create_note, thread_sensitive=True)
#
# ЧОМУ НЕ просто async def з native ORM?
# ──────────────────────────────────────
# create_note() в services.py використовує:
#   with transaction.atomic():
#       note = Note.objects.create(...)
#       note.tags.set(valid_tags)    ← M2M всередині транзакції
#
# Транзакції з transaction.atomic() поки не підтримуються нативно в async-режимі Django.
# Якщо викликати create_note() напряму з async view — можливі помилки:
#   - SynchronousOnlyOperation (Django виявляє sync DB call у async контексті)
#   - Thread-safety порушення (DB-з'єднання не thread-safe між coroutines)
#
# РІШЕННЯ: sync_to_async()
# ────────────────────────
# sync_to_async(fn) обгортає sync функцію так, що:
#   1. Async view викликає await async_create_note(...)
#   2. Event loop призупиняє coroutine (і обслуговує ІНШІ запити)
#   3. Django запускає create_note() у виділеному sync потоці
#   4. Sync потік виконує transaction.atomic() + ORM без проблем
#   5. Потік повертає результат → event loop відновлює view
#
# thread_sensitive=True (за замовчуванням):
#   Всі sync_to_async виклики з одного запиту йдуть в ОДИН і той самий потік.
#   Важливо для Django ORM: DB-з'єднання прив'язане до потоку.

async_create_note = sync_to_async(create_note, thread_sensitive=True)
"""
Async-обгортка для services.create_note().

Використання у view:
    note = await async_create_note(
        user=request.user,
        title="Назва",
        content="Зміст",
        priority=1,
    )

Синтаксис: той самий, що й create_note() — всі аргументи keyword-only.
Sync-аналог: services.create_note() — docs: services.py:13
"""


# ─────────────────────────────────────────────────────────────────────────────
# DELETE — native async ORM (не потребує sync_to_async)
# ─────────────────────────────────────────────────────────────────────────────

async def async_delete_note(note):
    """
    Видаляє нотатку асинхронно через native Django async ORM.

    Sync-аналог: services.delete_note() → note.delete()

    ЧОМУ НЕ sync_to_async тут?
    ───────────────────────────
    delete_note() в services.py просто робить note.delete() — без транзакцій,
    без складної логіки. Django 5.x надає async-аналог: note.adelete().

    adelete() — нативна async операція:
      - не потребує sync_to_async
      - передає управління event loop'у поки DB виконує DELETE
      - повертає (кількість_видалених, {model: кількість})

    Порівняй:
      Sync:  note.delete()   → блокує потік
      Async: await note.adelete() → звільняє event loop
    """
    # await тут: adelete() реально йде до бази. Event loop вільний поки DB відповідає.
    await note.adelete()


# ─────────────────────────────────────────────────────────────────────────────
# TOGGLE PIN — native async ORM через aupdate + F expression
# ─────────────────────────────────────────────────────────────────────────────

async def async_toggle_pin_note(note):
    """
    Перемикає is_pinned нотатки (True→False, False→True) асинхронно.

    Sync-аналог: services.toggle_pin_note() → Note.objects.filter(...).update(is_pinned=~F(...))

    ЧОМУ aupdate замість asave?
    ────────────────────────────
    Два підходи до зміни поля:

    Варіант 1 — через asave() (менш ефективний):
        note.is_pinned = not note.is_pinned
        await note.asave(update_fields=['is_pinned'])
        # Потребує два рядки. is_pinned читається з пам'яті (може бути race condition).

    Варіант 2 — через aupdate() + F() (ефективніший, атомарний):
        await Note.objects.filter(pk=note.pk).aupdate(is_pinned=~F('is_pinned'))
        # Один SQL запит: UPDATE note SET is_pinned = NOT is_pinned WHERE pk=...
        # F('is_pinned') читає значення з БД (не з пам'яті) — атомарно.
        # Захищає від race condition при одночасних запитах.

    aupdate() — async-аналог .update():
      - виконує UPDATE SQL напряму (без завантаження об'єкта)
      - атомарна операція на рівні БД
      - F() дозволяє посилатись на поточне значення поля в БД

    Документація F expressions: https://docs.djangoproject.com/en/5.2/ref/models/expressions/#f-expressions
    """
    # F('is_pinned') → посилання на поточне значення в БД
    # ~F(...)        → Django генерує NOT is_pinned у SQL
    # aupdate()      → async UPDATE, event loop вільний поки DB відповідає
    await Note.objects.filter(pk=note.pk).aupdate(is_pinned=~F('is_pinned'))
