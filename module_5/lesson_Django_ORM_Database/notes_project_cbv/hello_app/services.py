"""
services.py — Шар ЗАПИСУ та бізнес-логіки (CREATE / UPDATE / DELETE)

════════════════════════════════════════════════════════════════════
ЩО ТАКЕ SERVICES? (Services/Selectors архітектура)
════════════════════════════════════════════════════════════════════

Сервіс — це функція що виконує одну бізнес-операцію.
Вона ЗМІНЮЄ стан бази даних: INSERT, UPDATE, DELETE.

Навіщо виносити бізнес-логіку з View?

БЕЗ SERVICES (погано):
  def note_create(request):                    # views.py
      if request.method == 'POST':
          with transaction.atomic():           # транзакції у View?!
              note = Note.objects.create(...)  # бізнес-логіка у View?!
              note.tags.set(...)               # M:N у View?!
              ...
  # Якщо ця ж логіка потрібна в API → копіпаст!
  # Якщо ця ж логіка потрібна в Celery → копіпаст!

З SERVICES (добре):
  def note_create(request):              # views.py — тільки HTTP!
      ...
      note = services.create_note(...)   # одна лінія
      return redirect(...)

  def create_note(*, user, title, ...):  # services.py — логіка тут
      with transaction.atomic():
          note = Note.objects.create(...)
          note.tags.set(...)
      return note
  # Використовуємо в View, API, Celery Task, тестах — скрізь однаково!

Правила:
  ✓ Services можуть ЧИТАТИ дані (через selectors або прямо)
  ✓ Services можуть ЗМІНЮВАТИ дані (INSERT/UPDATE/DELETE)
  ✓ Атомарні операції обгортаємо в transaction.atomic()
  ✗ Services НЕ мають знати про HTTP (request, response, redirect, render)
  ✗ Services НЕ повертають HttpResponse
  ✗ Services НЕ читають request.user (приймають user як аргумент)

════════════════════════════════════════════════════════════════════
КЛЮЧОВІ КОНЦЕПЦІЇ В ЦЬОМУ ФАЙЛІ:
════════════════════════════════════════════════════════════════════

  transaction.atomic():
  → SQL: BEGIN; ... COMMIT; (або ROLLBACK при винятку)
  → Гарантує: або всі операції збережуться, або жодна

  save(update_fields=['title', 'content'])
  → SQL: UPDATE note SET title=?, content=? WHERE id=?
  → Оновлює ТІЛЬКИ вказані поля (не всі!)
  → Краще для продуктивності на широких таблицях

  F('is_pinned')
  → SQL: UPDATE note SET is_pinned = NOT is_pinned WHERE id=?
  → Атомарно на рівні БД — без race condition

  select_for_update()
  → SQL: SELECT ... FOR UPDATE (блокує рядок)
  → Запобігає одночасній зміні одного рядка двома запитами

  Tag.objects.get_or_create(user=user, name=name)
  → SQL: SELECT або INSERT (атомарно через UNIQUE constraint)
  → Безпечно від race condition при одночасному створенні

  .update(is_pinned=True) — масове оновлення без завантаження об'єктів
  → SQL: UPDATE ... WHERE id IN (...)
  → Набагато ефективніше ніж: for obj in qs: obj.save()
"""
from django.db import transaction
from django.db.models import F, Max
from django.utils import timezone

from .models import Note, Notebook, Tag, TodoList, TodoItem, ShoppingList, ShopItem, Reminder


# ─────────────────────────────────────────────────────────────────────────────
# NOTE SERVICES
# ─────────────────────────────────────────────────────────────────────────────

def create_note(*, user, title, content='', notebook=None, priority=1, tag_ids=None):
    """
    Створення нотатки разом з тегами (атомарна операція).

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Крок 1: transaction.atomic()
      SQL: BEGIN;
      Якщо будь-яка операція всередині кине Exception → ROLLBACK.
      Гарантія: або Note І теги збережені, або НІЧОГО.

      Без atomic():
        note = Note.objects.create(...)  # SQL: INSERT → OK
        note.tags.set(...)               # SQL: INSERT → Exception!
        # Результат: note існує в БД, але без тегів. Некоректний стан!

      З atomic():
        → Exception у tags.set() → автоматичний ROLLBACK на Note теж!
        → БД залишається у консистентному стані

    Крок 2: Note.objects.create(...)
      SQL: INSERT INTO hello_app_note (user_id, title, content, notebook_id, priority, ...)
           VALUES (1, 'Назва', 'Вміст', NULL, 1, ...)
           RETURNING id, created_at, updated_at, ...

      Всі nullable поля (notebook=None, content='') — безпечно:
        notebook=None → SQL: notebook_id = NULL

    Крок 3: Tag.objects.filter(id__in=tag_ids, user=user)
      ВАЖЛИВО: фільтр по user=user!
      Без цього: Alice може передати id тега Bob'а → зв'язок з чужим тегом!
      З фільтром: тільки теги що ДІЙСНО належать цьому юзеру

    Крок 4: note.tags.set(valid_tags)
      SQL: DELETE FROM hello_app_note_tags WHERE note_id = <note.id>
           INSERT INTO hello_app_note_tags (note_id, tag_id) VALUES (...)
      .set() = "замінити всі теги на вказані"
      Це безпечно: при CREATE нотатка ще не має тегів → тільки INSERT

    Крок 5: return note
      SQL: COMMIT;
      Повертаємо збережений об'єкт (з id, created_at тощо)

    ════════════════════════════════════════════════════════════════
    ТІЛЬКИ KEYWORD ARGUMENTS (зірочка *):
    ════════════════════════════════════════════════════════════════

    Визначення: create_note(*, user, title, ...)
    Виклик: services.create_note(user=request.user, title="...")  ← так!
    Виклик: services.create_note(request.user, "Назва")           ← ПОМИЛКА!

    Чому? Keyword-only args = явний, читабельний виклик.
    При рефакторингу (зміна порядку аргументів) → не зламаємо існуючий код.

    Args:
        user: auth.User instance — автор нотатки
        title: str — заголовок (обов'язковий)
        content: str — вміст (default: порожній рядок)
        notebook: Notebook instance або None (default: None)
        priority: int 1-4 (default: 1 — низький)
        tag_ids: list[int] або None — id тегів що належать user

    Returns:
        Note instance (збережений, з id та timestamps)
    """
    with transaction.atomic():
        # ── Крок 1: CREATE нотатку ──────────────────────────────────────────
        note = Note.objects.create(
            user=user,            # FK → user.id (не приймаємо user_id напряму!)
            title=title,
            content=content,
            notebook=notebook,    # None → notebook_id = NULL у БД
            priority=priority,
        )

        # ── Крок 2: Прив'язати теги (M:N) ───────────────────────────────────
        if tag_ids:
            # Фільтрація по user — ЗАХИСТ від підстановки чужих тегів!
            valid_tags = Tag.objects.filter(id__in=tag_ids, user=user)
            # .set() замінює всі теги новим набором
            note.tags.set(valid_tags)

    return note
    # Після виходу з with → SQL: COMMIT (або ROLLBACK якщо виняток)


def update_note(note, *, title=None, content=None, priority=None,
                notebook=None, is_pinned=None, tag_ids=None):
    """
    Часткове оновлення нотатки (тільки вказані поля).

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Патерн "часткового оновлення" (Partial Update):
      - Якщо аргумент = None → поле НЕ оновлюється
      - Якщо аргумент вказано → поле оновлюється

    Чому важливо save(update_fields=...)?

    БЕЗ update_fields:
      note.title = "Новий заголовок"
      note.save()
      SQL: UPDATE note SET title=?, content=?, priority=?, is_pinned=?,
                          is_archived=?, notebook_id=?, updated_at=?
           WHERE id=?
      → Оновлює ВСІ поля, навіть ті що не змінились!
      → Небезпечно: може перезаписати зміни що відбулись паралельно

    З update_fields:
      note.save(update_fields=['title', 'updated_at'])
      SQL: UPDATE note SET title=?, updated_at=? WHERE id=?
      → Оновлює ТІЛЬКИ вказані поля
      → Безпечніше, швидше, точніше

    Крок 1: Збираємо список змінених полів
      changed_fields = [] — починаємо порожнім
      Для кожного аргументу: якщо передано → встановлюємо + додаємо до списку

    Крок 2: note.save(update_fields=changed_fields)
      Виконується тільки якщо є що оновлювати.
      Якщо changed_fields = [] → save взагалі не викликається (немає зайвого SQL)

    Крок 3: Теги — окрема операція
      if tag_ids is not None (не [], а None!):
        → Якщо tag_ids = [] → очищаємо всі теги
        → Якщо tag_ids = [1, 2] → замінюємо теги на ці два
        → Якщо tag_ids = None → НЕ ЗМІНЮЄМО теги (параметр не передано)

    Args:
        note: Note instance (вже завантажений з БД)
        title: str або None
        content: str або None
        priority: int або None
        notebook: Notebook або None (None тут = "не змінювати", не "прибрати")
        is_pinned: bool або None
        tag_ids: list[int] або None (None = не змінювати, [] = прибрати всі)

    Returns:
        Note instance (оновлений)
    """
    changed_fields = []

    # ── Для кожного поля: перевіряємо чи передано → встановлюємо ──────────
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
        # Примітка: None тут значить "не передано", не "прибрати записник"
        # Для "прибрати записник" потрібен спеціальний sentinel або окрема функція
        note.notebook = notebook
        changed_fields.append('notebook')

    # ── Зберігаємо тільки якщо є зміни ─────────────────────────────────────
    if changed_fields:
        # updated_at оновлюється автоматично (auto_now=True) при будь-якому save()
        note.save(update_fields=changed_fields)

    # ── Теги: окрема операція (M:N не в update_fields) ──────────────────────
    if tag_ids is not None:
        # Важливо: tag_ids=[] → очищаємо всі теги (set порожнім набором)
        valid_tags = Tag.objects.filter(id__in=tag_ids, user=note.user)
        note.tags.set(valid_tags)
        # SQL: DELETE FROM note_tags WHERE note_id=?
        #      INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?), ...

    return note


def toggle_pin_note(note):
    """
    Перемкнути закріплення нотатки (атомарно).

    ════════════════════════════════════════════════════════════════
    ЧОМ ВИКОРИСТОВУЄМО F() А НЕ PYTHON TOGGLE?
    ════════════════════════════════════════════════════════════════

    БЕЗ F() (race condition!):
      note = Note.objects.get(pk=pk)   # SELECT: is_pinned = False
      note.is_pinned = not note.is_pinned  # Python: True
      note.save()                       # UPDATE: is_pinned = True
      # Проблема: між SELECT і UPDATE інший запит міг вже змінити is_pinned!

    З F() (атомарно):
      Note.objects.filter(pk=pk).update(is_pinned=~F('is_pinned'))
      SQL: UPDATE note SET is_pinned = NOT is_pinned WHERE id = ?
      → Одна SQL операція, на рівні БД, без race condition!

    Крок 2: refresh_from_db(fields=['is_pinned'])
      Оновлює тільки is_pinned у Python-об'єкті після update().
      Без цього: note.is_pinned у пам'яті = старе значення!

    Args:
        note: Note instance

    Returns:
        Note instance з оновленим is_pinned
    """
    # Атомарний toggle на рівні БД: NOT is_pinned
    Note.objects.filter(pk=note.pk).update(is_pinned=~F('is_pinned'))
    # Оновлюємо Python-об'єкт (після .update() Python-об'єкт не оновлюється автоматично!)
    note.refresh_from_db(fields=['is_pinned'])
    return note


def archive_note(note):
    """
    Архівувати нотатку (soft delete — не видаляти, лише приховати).

    Чому archive замість delete?
    → Користувач може відновити нотатку пізніше
    → Збереження даних (audit trail)
    → UX: випадкові видалення = критичний UX-баг

    SQL: UPDATE note SET is_archived = TRUE WHERE id = ?
    """
    Note.objects.filter(pk=note.pk).update(is_archived=True)
    # .update() на окремому Filter — не потрібно SELECT + save()
    # Більш ефективно для одного поля


def unarchive_note(note):
    """
    Відновити нотатку з архіву.
    SQL: UPDATE note SET is_archived = FALSE WHERE id = ?
    """
    Note.objects.filter(pk=note.pk).update(is_archived=False)


def delete_note(note):
    """
    Видалити нотатку назавжди (hard delete).

    CASCADE в БД автоматично видалить пов'язані записи:
      → Reminder (on_delete=CASCADE)

    M:N теги: Django автоматично видалить записи з junction table
      → hello_app_note_tags WHERE note_id = ?

    ЩО НЕ видалиться (on_delete=SET_NULL):
      → Notebook: notebook.notes залишаться, але note.notebook → NULL

    Args:
        note: Note instance

    Returns:
        None (об'єкт більше не існує в БД)
    """
    note.delete()
    # SQL: DELETE FROM hello_app_note WHERE id = ?
    # + автоматичний CASCADE для Reminder
    # + автоматичне очищення hello_app_note_tags (M:N junction)


# ─────────────────────────────────────────────────────────────────────────────
# NOTEBOOK SERVICES
# ─────────────────────────────────────────────────────────────────────────────

def create_notebook(*, user, title, color='#4A90E2', is_default=False):
    """
    Створення записника. Якщо is_default=True — скидаємо default у інших.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Бізнес-правило: може бути ТІЛЬКИ ОДИН записник за замовчуванням.
    Якщо новий записник встановлюємо як default → знімаємо у решти.

    Крок 1: transaction.atomic() — обидві операції атомарно
      Якщо CREATE упаде після UPDATE → попередній default залишиться скинутим!
      З atomic() → або обидві, або жодна.

    Крок 2: Якщо is_default=True:
      Notebook.objects.filter(user=user, is_default=True).update(is_default=False)
      SQL: UPDATE notebook SET is_default = FALSE WHERE user_id=1 AND is_default=TRUE
      → Один SQL запит для всіх записників (не N save()!)

    Крок 3: Notebook.objects.create(...)
      SQL: INSERT INTO hello_app_notebook (...) VALUES (...)

    Args:
        user: auth.User instance
        title: str — назва записника
        color: str — HEX колір (default: синій)
        is_default: bool — чи є записником за замовчуванням

    Returns:
        Notebook instance (збережений)
    """
    with transaction.atomic():
        if is_default:
            # Скидаємо is_default у ВСІХ інших записників цього юзера
            # .update() → один SQL замість циклу з save()
            Notebook.objects.filter(
                user=user,
                is_default=True
            ).update(is_default=False)

        return Notebook.objects.create(
            user=user,
            title=title,
            color=color,
            is_default=is_default,
        )


def update_notebook(notebook, *, title, description='', color, is_default):
    """
    Оновлення записника з атомарним скиданням флагу is_default.

    ════════════════════════════════════════════════════════════════
    БІЗНЕС-ПРАВИЛО:
    ════════════════════════════════════════════════════════════════

    Якщо is_default=True → цей записник стає єдиним default:
      1. UPDATE notebook SET is_default=False WHERE user=user AND id!=notebook.id
      2. UPDATE notebook SET title=..., is_default=True WHERE id=notebook.id

    Крок 1 та 2 в transaction.atomic() → атомарно.

    Часткове оновлення через save(update_fields=...):
      Оновлюємо ТІЛЬКИ змінені поля → мінімальне навантаження на БД.
      SQL: UPDATE SET title=?, description=?, color=?, is_default=? WHERE id=?

    Args:
        notebook: Notebook instance
        title: str — нова назва
        description: str — новий опис
        color: str — HEX колір
        is_default: bool — чи є записником за замовчуванням
    Returns:
        Notebook instance (оновлений)
    """
    with transaction.atomic():
        if is_default and not notebook.is_default:
            # Скидаємо is_default у всіх ІНШИХ записників цього юзера
            Notebook.objects.filter(
                user=notebook.user,
                is_default=True
            ).exclude(pk=notebook.pk).update(is_default=False)

        notebook.title = title
        notebook.description = description
        notebook.color = color
        notebook.is_default = is_default
        # save(update_fields=) → UPDATE тільки цих полів, не всього рядка
        notebook.save(update_fields=['title', 'description', 'color', 'is_default'])
        return notebook


def delete_notebook(notebook):
    """
    Видалення записника.

    ════════════════════════════════════════════════════════════════
    ЩО ВІДБУВАЄТЬСЯ ПРИ ВИДАЛЕННІ?
    ════════════════════════════════════════════════════════════════

    Notebook → Note (on_delete=SET_NULL):
      Всі нотатки цього записника: notebook_id → NULL
      Нотатки НЕ видаляються — тільки від'єднуються від записника!

    SQL: DELETE FROM hello_app_notebook WHERE id=?
    Django автоматично:
      UPDATE hello_app_note SET notebook_id=NULL WHERE notebook_id=?

    Args:
        notebook: Notebook instance для видалення
    """
    notebook.delete()
    # Після delete(): notebook.pk = None (Django скидає PK видаленого об'єкта)


# ─────────────────────────────────────────────────────────────────────────────
# TAG SERVICES
# ─────────────────────────────────────────────────────────────────────────────

def create_or_get_tag(*, user, name, color='#808080'):
    """
    Отримати тег або створити якщо не існує (idempotent операція).

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Крок 1: Tag.objects.get_or_create(...)
      Django реалізує це атомарно:
        1. Спробуй SELECT де user=user AND name=name
        2. Якщо знайдено → повернути (tag, False)
        3. Якщо не знайдено → INSERT → повернути (tag, True)

      При race condition (два запити одночасно намагаються створити #python):
        → UNIQUE constraint на (user, name) → IntegrityError
        → Django обробляє: другий запит отримує існуючий тег

    Крок 2: name.lower().strip()
      → нормалізація: "  Python  " → "python"
      → '#Python' і '#python' = один тег (не дублі!)

    Крок 3: defaults={'color': color}
      → якщо тег ІСНУЄ → color НЕ оновлюється (лише при CREATE)
      → defaults = поля що встановлюються тільки при створенні

    Приклад використання:
      tag, created = services.create_or_get_tag(
          user=user, name='python', color='#3776AB'
      )
      if created:
          print(f"Новий тег: #{tag.name}")
      else:
          print(f"Тег вже існував: #{tag.name}")

    Args:
        user: auth.User instance
        name: str — назва тегу (буде lowercase і stripped)
        color: str — HEX колір (використовується ТІЛЬКИ при CREATE)

    Returns:
        tuple[Tag, bool]: (tag, True якщо створено, False якщо вже існував)
    """
    tag, created = Tag.objects.get_or_create(
        user=user,
        name=name.lower().strip(),  # нормалізація: "Python" → "python"
        defaults={'color': color}   # defaults використовуються тільки при CREATE
        # Пошук відбувається по: user + name
    )
    return tag, created


# ─────────────────────────────────────────────────────────────────────────────
# TODO SERVICES
# ─────────────────────────────────────────────────────────────────────────────

def create_todo_list(*, user, title, description=''):
    """
    Створення нового списку справ.

    Простий CREATE — без транзакції (одна операція).

    Args:
        user: auth.User instance
        title: str — назва списку
        description: str — опис (default: порожній)

    Returns:
        TodoList instance
    """
    return TodoList.objects.create(user=user, title=title, description=description)


def add_todo_item(*, todo_list, text, due_date=None):
    """
    Додати пункт у список справ з правильним порядком.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Бізнес-правило: нові пункти додаються В КІНЕЦЬ списку.
    order_position = max(існуючих) + 1

    Крок 1: aggregate(max_pos=Max('order_position'))
      SQL: SELECT MAX(order_position) FROM hello_app_todoitem
           WHERE todo_list_id = ?
      → Повертає {'max_pos': 3} або {'max_pos': None} якщо список порожній
      → or 0: якщо None → 0 (для першого пункту → position=1)

    Крок 2: TodoItem.objects.create(... order_position=last_position + 1)
      → Новий пункт завжди після всіх існуючих

    Чому не auto-increment?
      order_position не є PRIMARY KEY — він може змінюватись при drag-and-drop.
      Потрібна гнучкість перевпорядкування без зміни PK.

    Args:
        todo_list: TodoList instance
        text: str — текст пункту
        due_date: date або None — дедлайн

    Returns:
        TodoItem instance
    """
    # ── Знаходимо останню позицію ────────────────────────────────────────────
    last_position = todo_list.items.aggregate(
        max_pos=Max('order_position')  # MAX() агрегація
    )['max_pos'] or 0  # None (порожній список) → 0

    # ── Створюємо з наступною позицією ──────────────────────────────────────
    return TodoItem.objects.create(
        todo_list=todo_list,
        text=text,
        order_position=last_position + 1,  # завжди в кінці
        due_date=due_date,
    )


def toggle_todo_item(item_id, *, user):
    """
    Відмітити/зняти відмітку пункту списку справ.

    ════════════════════════════════════════════════════════════════
    ЧОМУ select_for_update()?
    ════════════════════════════════════════════════════════════════

    Сценарій без блокування (race condition):
      User A: SELECT item WHERE id=5 → is_done=False
      User B: SELECT item WHERE id=5 → is_done=False (те ж значення!)
      User A: UPDATE item SET is_done=True WHERE id=5
      User B: UPDATE item SET is_done=True WHERE id=5  ← теж True!
      Результат: обидва бачать is_done=True, хоча другий клік мав би зняти

    З select_for_update():
      User A: SELECT item WHERE id=5 FOR UPDATE  → отримує блокування
      User B: SELECT item WHERE id=5 FOR UPDATE  → ЧЕКАЄ поки A завершить
      User A: UPDATE item SET is_done=True; COMMIT → знімає блокування
      User B: SELECT → тепер бачить is_done=True → toggle → is_done=False
      Результат: коректна почергова обробка!

    Крок 1: transaction.atomic() — обов'язково для select_for_update()
      select_for_update() без atomic() → TransactionManagementError!

    Крок 2: select_for_update().get(id=item_id, todo_list__user=user)
      → Блокує рядок на час транзакції
      → todo_list__user=user: traversal FK для перевірки права доступу
        SQL: WHERE item.id=? AND todolist.user_id=?
        (JOIN hello_app_todolist ON item.todo_list_id = todolist.id)

    Крок 3: toggle is_done, save(update_fields=['is_done'])
      → Оновлюємо тільки is_done (не all fields)

    Args:
        item_id: int — ID пункту
        user: auth.User instance (для перевірки права доступу)

    Returns:
        TodoItem instance з оновленим is_done

    Raises:
        TodoItem.DoesNotExist: якщо item не знайдено або не належить user
    """
    with transaction.atomic():
        # select_for_update() = SELECT ... FOR UPDATE (блокування рядка)
        item = TodoItem.objects.select_for_update().get(
            id=item_id,
            todo_list__user=user   # traversal: item → todo_list → user (security!)
        )
        # Toggle: True → False або False → True
        item.is_done = not item.is_done
        item.save(update_fields=['is_done'])  # оновлюємо тільки це поле
    # Вихід з with → COMMIT → знімає блокування рядка
    return item


def complete_todo_list(todo_list):
    """
    Позначити весь список справ як завершений.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Крок 1: transaction.atomic() — дві операції атомарно
      1. todo_list.is_completed = True (позначити список)
      2. items.update(is_done=True) (позначити всі пункти)
      Обидві → або обидві, або жодна.

    Крок 2: items.filter(is_done=False).update(is_done=True)
      SQL: UPDATE todoitem SET is_done = TRUE
           WHERE todo_list_id = ? AND is_done = FALSE
      → filter(is_done=False): оновлюємо тільки незавершені (оптимізація)
      → .update(): один SQL запит, не N save()

    Args:
        todo_list: TodoList instance
    """
    with transaction.atomic():
        # Позначаємо список як завершений
        todo_list.is_completed = True
        todo_list.save(update_fields=['is_completed'])

        # Масово позначаємо ВСІ незавершені пункти як виконані
        # .update() → один SQL для N рядків (набагато ефективніше за цикл!)
        todo_list.items.filter(is_done=False).update(is_done=True)


# ─────────────────────────────────────────────────────────────────────────────
# SHOPPING SERVICES
# ─────────────────────────────────────────────────────────────────────────────

def create_shopping_list(*, user, title, store_name=''):
    """
    Створення нового списку покупок.

    Args:
        user: auth.User instance
        title: str — назва (наприклад: "Продукти на тиждень")
        store_name: str — назва магазину (default: порожній)

    Returns:
        ShoppingList instance
    """
    return ShoppingList.objects.create(
        user=user,
        title=title,
        store_name=store_name,
    )


def add_shop_item(*, shopping_list, name, quantity=1, unit='шт', estimated_price=None):
    """
    Додати товар у список покупок.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Крок 1: ShopItem.objects.create(...)
      SQL: INSERT INTO hello_app_shopitem
           (shopping_list_id, name, quantity, unit, estimated_price, is_purchased)
           VALUES (?, ?, ?, ?, ?, FALSE)

    quantity і estimated_price: DecimalField!
      quantity=1 → Decimal('1') (точна арифметика)
      estimated_price=None → NULL у БД (ціна невідома)

    CheckConstraint 'shop_item_positive_quantity' у БД:
      → quantity > 0 перевіряється навіть якщо Django валідацію обійти!
      → SQL: CONSTRAINT ... CHECK (quantity > 0)
      → При quantity<=0 → IntegrityError!

    Args:
        shopping_list: ShoppingList instance
        name: str — назва товару
        quantity: Decimal/int/float — кількість (default: 1)
        unit: str — одиниця виміру: 'шт', 'кг', 'л', 'г'
        estimated_price: Decimal або None — орієнтовна ціна

    Returns:
        ShopItem instance
    """
    return ShopItem.objects.create(
        shopping_list=shopping_list,
        name=name,
        quantity=quantity,
        unit=unit,
        estimated_price=estimated_price,  # None → NULL (ціна невідома)
    )


def mark_item_purchased(item_id, *, user):
    """
    Відмітити товар як куплений.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    .update() замість select + save:
      БЕЗ: item = ShopItem.objects.get(id=item_id)   # SELECT
            item.is_purchased = True
            item.save()                               # UPDATE всіх полів
      З:   ShopItem.objects.filter(id=item_id).update(is_purchased=True)
            SQL: UPDATE shopitem SET is_purchased = TRUE WHERE id = ?
            → 1 запит замість 2
            → Оновлює тільки is_purchased

    Перевірка права доступу через FK traversal:
      filter(id=item_id, shopping_list__user=user)
      SQL WHERE: shopitem.id=? AND shoppinglist.user_id=?
      → Без JOIN у Python — Django генерує JOIN або subquery

    Args:
        item_id: int — ID товару
        user: auth.User instance (для перевірки права доступу)

    Returns:
        None (якщо товар не знайдено або не належить user → оновлення 0 рядків)
    """
    ShopItem.objects.filter(
        id=item_id,
        shopping_list__user=user  # FK traversal: security check
    ).update(is_purchased=True)


# ─────────────────────────────────────────────────────────────────────────────
# REMINDER SERVICES
# ─────────────────────────────────────────────────────────────────────────────

def create_reminder(*, note, remind_at, message='', repeat_pattern='none'):
    """
    Створити нагадування для нотатки.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    remind_at — datetime у UTC (timezone.now() теж UTC)
    Важливо: зберігати в UTC, конвертувати в local timezone тільки при показі.

    is_sent=False (default у моделі) — Celery task відправить пізніше:
      selectors.get_pending_reminders() → знайде незавершені
      services.mark_reminder_sent(id) → позначить після відправлення

    Args:
        note: Note instance — до якої нотатки прив'язане нагадування
        remind_at: datetime — коли відправити (UTC!)
        message: str — текст нагадування (default: порожній)
        repeat_pattern: str — 'none'|'daily'|'weekly'|'monthly'

    Returns:
        Reminder instance
    """
    return Reminder.objects.create(
        note=note,
        remind_at=remind_at,       # UTC datetime
        message=message,
        repeat_pattern=repeat_pattern,
        # is_sent=False — за замовчуванням у моделі
    )


def mark_reminder_sent(reminder_id):
    """
    Атомарно позначити нагадування як відправлене.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Викликається з Celery task після успішного відправлення email:
      @shared_task
      def send_pending_reminders():
          for reminder in selectors.get_pending_reminders():
              try:
                  send_email(to=reminder.note.user.email, ...)
                  services.mark_reminder_sent(reminder.id)  ← тут
              except Exception:
                  pass  # наступна ітерація спробує знову

    Чому .update() замість .get() + .save()?
      .update() = 1 SQL запит, атомарно
      .get() + .save() = 2 SQL запити + потенційний race condition

    SQL: UPDATE reminder SET is_sent = TRUE WHERE id = ?

    Args:
        reminder_id: int — ID нагадування

    Returns:
        None
    """
    Reminder.objects.filter(pk=reminder_id).update(is_sent=True)
    # Якщо reminder_id не знайдено → оновлення 0 рядків (не Exception!)
    # Це ідемпотентна операція: виклик двічі → той самий стан
