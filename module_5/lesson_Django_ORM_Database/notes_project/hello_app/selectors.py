"""
selectors.py — Шар ЧИТАННЯ даних (SELECT queries)

════════════════════════════════════════════════════════════════════
ЩО ТАКЕ SELECTORS? (Services/Selectors архітектура)
════════════════════════════════════════════════════════════════════

Селектор — це функція що ТІЛЬКИ читає дані з БД і повертає QuerySet або об'єкт.
Вона НІКОЛИ не змінює дані (немає INSERT/UPDATE/DELETE).

Навіщо виносити QuerySets у окремий модуль?

БЕЗ SELECTORS (погано):
  def note_list(request):                          # views.py
      notes = Note.objects.filter(                 # QuerySet прямо у View!
          user=request.user,
          is_archived=False
      ).select_related('notebook')                 # якщо забути → N+1 на кожній сторінці
      ...

З SELECTORS (добре):
  def note_list(request):                          # views.py (тонкий)
      notes = selectors.get_user_notes(request.user)  # одна лінія

  def get_user_notes(user, ...):                   # selectors.py (вся оптимізація тут)
      return Note.objects.filter(...).select_related(...)  # змінив один раз → скрізь

Переваги:
  ✓ Один раз написав select_related → автоматично у View, API, Celery Task
  ✓ Бізнес-логіка фільтрації в одному місці
  ✓ Легко тестувати: get_user_notes(user, search="test") без HTTP request
  ✓ View залишається "тонким" (тільки HTTP: request/response)

════════════════════════════════════════════════════════════════════
КЛЮЧОВІ ORM КОНЦЕПЦІЇ В ЦЬОМУ ФАЙЛІ:
════════════════════════════════════════════════════════════════════

  select_related('notebook')
  → SQL: LEFT OUTER JOIN hello_app_notebook ON (...)
  → Замість N+1 → 1 запит для Note + Notebook

  prefetch_related('tags')
  → SQL: SELECT * FROM hello_app_tag WHERE id IN (...)
  → Замість N+1 для M:N → 2 запити (ніколи N+1)

  Prefetch('reminders', queryset=..., to_attr='upcoming_reminders')
  → Фільтрований prefetch + зберігає в кастомний атрибут
  → note.upcoming_reminders → list[Reminder] (не QuerySet!)

  Count('notes', filter=Q(notes__is_archived=False))
  → SQL: COUNT(notes.id) FILTER (WHERE notes.is_archived = FALSE)
  → Умовна агрегація в одному GROUP BY запиті

  Q(title__icontains=...) | Q(content__icontains=...)
  → SQL: WHERE (title ILIKE '%text%' OR content ILIKE '%text%')
  → Пошук по кількох полях

  'note__user'  (traversal через FK)
  → SQL: JOIN через дві таблиці
  → reminder → note → user (за один select_related)
"""
from django.db.models import Count, Q, Prefetch
from django.utils import timezone

from .models import Note, Notebook, Tag, TodoList, TodoItem, ShoppingList, Reminder


# ─────────────────────────────────────────────────────────────────────────────
# NOTE SELECTORS
# ─────────────────────────────────────────────────────────────────────────────

def get_user_notes(user, *, archived=False, notebook=None, tag=None, search=None):
    """
    Список нотаток користувача з фільтрами.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Крок 1: Базовий QuerySet — фільтр по юзеру та статусу архіву
      Note.objects.filter(user=user, is_archived=archived)
      SQL: WHERE note.user_id = %s AND note.is_archived = %s

      Чому is_archived=archived (not False жорстко)?
      Та сама функція повертає і архів і активні залежно від параметра.
      Виклик: get_user_notes(user) → активні
               get_user_notes(user, archived=True) → архів

    Крок 2: select_related('notebook') — вирішення N+1 для FK
      БЕЗ: for note in notes: print(note.notebook.title)
           → 1 SELECT для notes + N SELECT для notebook (по одному!)
      З:   SQL: SELECT note.*, nb.* FROM note LEFT JOIN notebook nb ON ...
           → 1 запит, всі дані вже в пам'яті

      Чому LEFT JOIN а не INNER JOIN?
      notebook може бути NULL! (нотатка без записника)
      → Django автоматично використовує LEFT OUTER JOIN

    Крок 3: prefetch_related('tags') — вирішення N+1 для M:N
      БЕЗ: for note in notes: print(note.tags.all())
           → 1 SELECT для notes + N SELECT для tags (по одному!)
      З:   ЗАПИТ 1: SELECT * FROM note WHERE ...
           ЗАПИТ 2: SELECT tag.* FROM tag INNER JOIN note_tags ON ...
                    WHERE note_tags.note_id IN (1, 2, 3, ..., 50)
           → 2 запити завжди, незалежно від кількості нотаток

    Крок 4: Ланцюгові фільтри (чому queryset лінивий)
      qs = Note.objects.filter(user=user)   # ← SQL ЩЕ НЕ ВИКОНАНО
      if notebook:
          qs = qs.filter(notebook=notebook)  # ← додаємо умову, SQL ЩЕ НЕ ВИКОНАНО
      if search:
          qs = qs.filter(Q(title__icontains=search))  # ← додаємо, SQL ЩЕ НЕ ВИКОНАНО
      return qs  # ← SQL виконається ТІЛЬКИ коли view ітерує results!

    Крок 5: Q-объект для OR умов
      Q(title__icontains=search) | Q(content__icontains=search)
      SQL: WHERE (note.title ILIKE '%search%' OR note.content ILIKE '%search%')

      Чому не filter(title__icontains=search, content__icontains=search)?
      Бо filter з кількома аргументами = AND, а нам потрібен OR!

    Крок 6: order_by('-is_pinned', '-priority', '-updated_at')
      SQL: ORDER BY is_pinned DESC, priority DESC, updated_at DESC
      Логіка: спочатку закріплені, потім по пріоритету, потім нові

    ════════════════════════════════════════════════════════════════
    ГЕНЕРОВАНИЙ SQL (приклад):
    ════════════════════════════════════════════════════════════════

      SELECT note.*, nb.id, nb.title, nb.color
      FROM hello_app_note note
      LEFT OUTER JOIN hello_app_notebook nb ON note.notebook_id = nb.id
      WHERE note.user_id = 1
        AND note.is_archived = FALSE
      ORDER BY note.is_pinned DESC, note.priority DESC, note.updated_at DESC
      LIMIT 50

      + окремий запит для prefetch:
      SELECT tag.*, nt.note_id FROM hello_app_tag tag
      INNER JOIN hello_app_note_tags nt ON tag.id = nt.tag_id
      WHERE nt.note_id IN (1, 2, 3, 4, 5, ...)

    Args:
        user: auth.User instance
        archived: якщо True — повертає заархівовані нотатки (default False)
        notebook: Notebook instance або None (фільтр по записнику)
        tag: Tag instance або None (фільтр по тегу)
        search: str або None (пошук в title та content)

    Returns:
        QuerySet[Note] — ЛІНИВИЙ! SQL виконається при ітерації в шаблоні.
    """
    # ── Крок 1: базовий фільтр ──────────────────────────────────────────────
    qs = Note.objects.filter(
        user=user,          # тільки нотатки цього користувача (ізоляція даних!)
        is_archived=archived  # True → архів, False → активні
    ).select_related(
        'notebook'          # FK: LEFT JOIN → 1 запит замість N
    ).prefetch_related(
        'tags'              # M:N: 2 запити замість N+1
    )

    # ── Крок 2: опційні фільтри (лінивий ланцюг) ────────────────────────────
    if notebook is not None:
        # Додаємо умову до існуючого QuerySet (SQL ще не виконується!)
        # SQL додасть: AND note.notebook_id = <notebook.pk>
        qs = qs.filter(notebook=notebook)

    if tag is not None:
        # filter(tags=tag) → Django генерує INNER JOIN через junction table:
        # AND EXISTS (SELECT 1 FROM hello_app_note_tags nt
        #             WHERE nt.note_id = note.id AND nt.tag_id = <tag.pk>)
        qs = qs.filter(tags=tag)

    if search:
        # Q-оператор: OR між двома умовами (якщо filter(A, B) → AND)
        # __icontains = case-insensitive LIKE '%search%'
        qs = qs.filter(
            Q(title__icontains=search) | Q(content__icontains=search)
        )

    # ── Крок 3: сортування ──────────────────────────────────────────────────
    # Негативний знак = DESC (спадання)
    # Порядок важливий: спочатку закріплені, потім пріоритет, потім дата
    return qs.order_by('-is_pinned', '-priority', '-updated_at')


def get_note_detail(user, note_id):
    """
    Деталь нотатки з усіма пов'язаними даними (оптимізовано).

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Крок 1: select_related('notebook', 'user')
      → 1 SQL з двома LEFT JOIN:
        SELECT note.*, nb.*, u.* FROM note
        LEFT JOIN notebook nb ON note.notebook_id = nb.id
        LEFT JOIN auth_user u ON note.user_id = u.id
        WHERE note.id = %s AND note.user_id = %s

    Крок 2: prefetch_related('tags')
      → окремий запит для M:N тегів

    Крок 3: Prefetch('reminders', queryset=FILTERED, to_attr='upcoming_reminders')
      → Фільтрований prefetch: завантажуємо НЕ всі нагадування,
        а тільки майбутні (remind_at >= зараз)
      → to_attr='upcoming_reminders': зберігаємо у кастомний атрибут

      БЕЗ to_attr:  note.reminders.all()          → QuerySet (ще один запит!)
      З to_attr:    note.upcoming_reminders        → list[Reminder] (вже в кеші!)

    Крок 4: .get(id=note_id, user=user)
      → GET одного об'єкта + security check:
        note.user = request.user гарантує що Alice не побачить нотатки Bob'а!
      → Якщо не знайдено → Note.DoesNotExist (View перехоплює → Http404)

    ════════════════════════════════════════════════════════════════
    ГЕНЕРОВАНИЙ SQL (3 запити):
    ════════════════════════════════════════════════════════════════

      -- Запит 1: основний об'єкт з JOIN
      SELECT note.*, nb.*, u.*
      FROM hello_app_note note
      LEFT OUTER JOIN hello_app_notebook nb ON note.notebook_id = nb.id
      INNER JOIN auth_user u ON note.user_id = u.id
      WHERE note.id = 42 AND note.user_id = 1

      -- Запит 2: теги через junction table
      SELECT tag.* FROM hello_app_tag tag
      INNER JOIN hello_app_note_tags nt ON tag.id = nt.tag_id
      WHERE nt.note_id = 42

      -- Запит 3: майбутні нагадування (фільтровані!)
      SELECT * FROM hello_app_reminder
      WHERE note_id = 42 AND remind_at >= NOW()
      ORDER BY remind_at ASC

    Raises:
        Note.DoesNotExist: якщо нотатка не знайдена або не належить user
        (View перетворює це на Http404)

    Returns:
        Note instance з:
          note.notebook        → вже завантажено (select_related)
          note.tags.all()      → вже в кеші (prefetch_related)
          note.upcoming_reminders → list[Reminder] (filtered Prefetch)
    """
    return Note.objects.select_related(
        'notebook',  # FK: замість note.notebook → окремий SELECT → JOIN
        'user'       # FK: потрібен для рендеру автора
    ).prefetch_related(
        'tags',      # M:N: 2 запити, не N+1

        # Prefetch з кастомним QuerySet — тільки МАЙБУТНІ нагадування!
        # Без цього: note.reminders.filter(remind_at__gte=now()) у шаблоні
        #            → окремий SELECT на кожну нотатку (N+1!)
        Prefetch(
            'reminders',  # related_name з моделі Reminder
            queryset=Reminder.objects.filter(
                remind_at__gte=timezone.now()  # тільки майбутні
            ).order_by('remind_at'),           # сортування по часу
            to_attr='upcoming_reminders'       # зберігаємо в цей атрибут
            # Доступ у шаблоні/view: note.upcoming_reminders (list, не QuerySet)
        )
    ).get(id=note_id, user=user)
    # .get() → викидає Note.DoesNotExist якщо немає → View → Http404
    # user=user → перевірка права доступу на рівні БД (не в Python!)


def get_pinned_notes(user, limit=5):
    """
    Закріплені нотатки для dashboard/sidebar.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Крок 1: filter(is_pinned=True, is_archived=False)
      → тільки активні закріплені нотатки

    Крок 2: select_related('notebook')
      → FK JOIN (для відображення назви записника в sidebar)

    Крок 3: prefetch_related('tags')
      → M:N (для відображення тегів без додаткових запитів)

    Крок 4: [:limit]  — SQL LIMIT
      → SELECT ... LIMIT 5
      → Python slice на QuerySet = SQL LIMIT, не Python slice!
      → Важливо для продуктивності: обмеження на рівні БД

    Args:
        user: auth.User instance
        limit: максимальна кількість нотаток (default 5)

    Returns:
        QuerySet[Note] обмежений до limit елементів
    """
    return Note.objects.filter(
        user=user,
        is_pinned=True,       # тільки закріплені
        is_archived=False     # не показуємо архівовані (навіть якщо закріплені)
    ).select_related('notebook').prefetch_related('tags')[:limit]
    # [:limit] → SQL: LIMIT 5 (не Python slice усього QuerySet!)


# ─────────────────────────────────────────────────────────────────────────────
# NOTEBOOK SELECTORS
# ─────────────────────────────────────────────────────────────────────────────

def get_user_notebooks(user):
    """
    Всі записники користувача з кількістю активних нотаток.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Крок 1: filter(user=user) — фільтр по власнику

    Крок 2: annotate(note_count=Count('notes', filter=...))
      → Умовна агрегація (Conditional COUNT):
        SQL: SELECT notebook.*,
               COUNT(note.id) FILTER (WHERE note.is_archived = FALSE)
               AS note_count
             FROM hello_app_notebook notebook
             LEFT JOIN hello_app_note note ON note.notebook_id = notebook.id
             WHERE notebook.user_id = 1
             GROUP BY notebook.id

      Чому не робити окремий запит для кожного записника?
        for notebook in notebooks:
            count = notebook.notes.filter(is_archived=False).count()
            # → N+1 проблема! 1 SELECT для notebooks + N SELECT для count

      З annotate: 1 SQL запит з GROUP BY → всі лічильники одразу!

    Крок 3: order_by('-is_default', 'title')
      → Записник за замовчуванням завжди першим (-is_default=DESC)
      → Решта по алфавіту

    У шаблоні доступ:
      {% for notebook in notebooks %}
          {{ notebook.title }} ({{ notebook.note_count }})
      {% endfor %}
      Нульових додаткових запитів! note_count вже в об'єкті.

    Args:
        user: auth.User instance

    Returns:
        QuerySet[Notebook] з анотованим полем note_count (int)
    """
    return Notebook.objects.filter(user=user).annotate(
        # Count('notes') — рахує по related_name 'notes' (з моделі Note)
        # filter=Q(...) — умовна агрегація: рахуємо тільки НЕ архівовані
        note_count=Count('notes', filter=Q(notes__is_archived=False))
        # notes__is_archived — traversal через FK: notes → is_archived
    ).order_by('-is_default', 'title')


# ─────────────────────────────────────────────────────────────────────────────
# TAG SELECTORS
# ─────────────────────────────────────────────────────────────────────────────

def get_user_tags(user):
    """
    Теги користувача з кількістю активних нотаток.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Крок 1: filter(user=user) — тільки теги цього юзера
      (Alice і Bob можуть мати теги з однаковою назвою, але це РІЗНІ теги)

    Крок 2: annotate(note_count=Count('notes', filter=...))
      → Умовна агрегація через M:N junction table!
      SQL: SELECT tag.*,
               COUNT(note.id) FILTER (WHERE note.is_archived = FALSE) AS note_count
           FROM hello_app_tag tag
           LEFT JOIN hello_app_note_tags nt ON tag.id = nt.tag_id
           LEFT JOIN hello_app_note note ON note.id = nt.note_id
             AND note.is_archived = FALSE
           WHERE tag.user_id = 1
           GROUP BY tag.id

      Важливо: Count через M:N потребує JOIN через junction table.
      Django генерує це автоматично!

    Крок 3: order_by('name') → алфавітне сортування

    У шаблоні:
      {% for tag in tags %}
          <span class="badge" style="background:{{ tag.color }}">
              #{{ tag.name }} ({{ tag.note_count }})
          </span>
      {% endfor %}

    Args:
        user: auth.User instance

    Returns:
        QuerySet[Tag] з анотованим полем note_count (int)
    """
    return Tag.objects.filter(user=user).annotate(
        # Count через M:N: Django автоматично генерує JOIN через junction table
        note_count=Count('notes', filter=Q(notes__is_archived=False))
    ).order_by('name')


# ─────────────────────────────────────────────────────────────────────────────
# TODO SELECTORS
# ─────────────────────────────────────────────────────────────────────────────

def get_user_todo_lists(user):
    """
    Списки справ з прогресом виконання.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Крок 1: filter(user=user) — тільки списки цього юзера

    Крок 2: annotate — ДВОХ анотації в одному запиті
      total_items: COUNT всіх пунктів
      done_items:  COUNT тільки виконаних пунктів

      SQL:
        SELECT todolist.*,
               COUNT(item.id) AS total_items,
               COUNT(item.id) FILTER (WHERE item.is_done = TRUE) AS done_items
        FROM hello_app_todolist todolist
        LEFT JOIN hello_app_todoitem item ON item.todo_list_id = todolist.id
        WHERE todolist.user_id = 1
        GROUP BY todolist.id

    Крок 3: prefetch_related('items')
      → Завантажуємо всі пункти (для детального відображення)
      → 2 запити: 1 для todo_lists + 1 для items (не N+1)

    Крок 4: order_by('is_completed', '-created_at')
      → Незавершені першими (is_completed=False=0 < True=1)
      → Новіші спочатку

    У шаблоні обчислення прогресу:
      {% if todo.total_items > 0 %}
          {% widthratio todo.done_items todo.total_items 100 %}%
      {% endif %}
      (або в Python: progress = done_items / total_items * 100)

    Args:
        user: auth.User instance

    Returns:
        QuerySet[TodoList] з total_items (int) та done_items (int)
    """
    return TodoList.objects.filter(
        user=user
    ).annotate(
        total_items=Count('items'),   # загальна кількість пунктів
        done_items=Count(             # тільки виконані
            'items',
            filter=Q(items__is_done=True)
        )
    ).prefetch_related('items').order_by('is_completed', '-created_at')


def get_todo_list_detail(user, todo_id):
    """
    Деталь списку справ з пунктами у правильному порядку.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Крок 1: prefetch_related з Prefetch(queryset=...) — КОНТРОЛЬ ПОРЯДКУ
      Без Prefetch: items у порядку що повертає БД (не гарантовано)
      З Prefetch: items відсортовані по order_position (drag-and-drop порядок)

    Крок 2: .get(id=todo_id, user=user) — перевірка права доступу
      → user=user: Alice не побачить списки Bob'а
      → TodoList.DoesNotExist якщо не знайдено

    У шаблоні:
      {% for item in todo_list.items.all %}
          Пункти вже відсортовані по order_position!
          Без додаткових запитів (в кеші prefetch).
      {% endfor %}

    Args:
        user: auth.User instance
        todo_id: int — ID списку справ

    Returns:
        TodoList instance з prefetched items (відсортованими)

    Raises:
        TodoList.DoesNotExist: якщо не знайдено або не належить user
    """
    return TodoList.objects.prefetch_related(
        Prefetch(
            'items',  # related_name='items' з моделі TodoItem
            queryset=TodoItem.objects.order_by(
                'order_position',  # порядок drag-and-drop
                'id'               # tie-breaker: стабільне сортування
            )
            # Без to_attr: todo_list.items.all() використовує кеш prefetch
        )
    ).get(id=todo_id, user=user)


# ─────────────────────────────────────────────────────────────────────────────
# SHOPPING SELECTORS
# ─────────────────────────────────────────────────────────────────────────────

def get_user_shopping_lists(user):
    """
    Списки покупок з кількістю ще не куплених товарів.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Крок 1: filter(user=user) — ізоляція даних між юзерами

    Крок 2: annotate — два лічильники в одному GROUP BY
      total_items:   COUNT всіх товарів
      pending_items: COUNT тільки НЕ куплених

    SQL:
      SELECT shoppinglist.*,
             COUNT(item.id) AS total_items,
             COUNT(item.id) FILTER (WHERE item.is_purchased = FALSE) AS pending_items
      FROM hello_app_shoppinglist shoppinglist
      LEFT JOIN hello_app_shopitem item ON item.shopping_list_id = shoppinglist.id
      WHERE shoppinglist.user_id = 1
      GROUP BY shoppinglist.id

    Порівняй з НЕПРАВИЛЬНИМ підходом:
      for sl in ShoppingList.objects.filter(user=user):
          total = sl.items.count()        # N запитів!
          pending = sl.items.filter(is_purchased=False).count()  # ще N!
          # Разом: 2N + 1 запитів замість 1!

    Args:
        user: auth.User instance

    Returns:
        QuerySet[ShoppingList] з total_items (int) та pending_items (int)
    """
    return ShoppingList.objects.filter(user=user).annotate(
        total_items=Count('items'),     # всі товари
        pending_items=Count(            # тільки некуплені
            'items',
            filter=Q(items__is_purchased=False)
        )
    ).order_by('-created_at')


# ─────────────────────────────────────────────────────────────────────────────
# REMINDER SELECTORS (для Celery worker або cron-задачі)
# ─────────────────────────────────────────────────────────────────────────────

def get_pending_reminders():
    """
    Нагадування що треба відправити зараз.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЯ ФУНКЦІЯ:
    ════════════════════════════════════════════════════════════════

    Ця функція викликається НЕ з View, а з Celery Task:
      @shared_task
      def send_pending_reminders():
          reminders = selectors.get_pending_reminders()
          for reminder in reminders:
              send_email(to=reminder.note.user.email, ...)
              services.mark_reminder_sent(reminder.id)

    Крок 1: filter(is_sent=False) — тільки ще НЕ відправлені
      Без цієї умови — відправляли б одне нагадування нескінченно!

    Крок 2: filter(remind_at__lte=timezone.now())
      → remind_at <= зараз: час прийшов
      → __lte = less than or equal (SQL: <=)
      → timezone.now() → UTC timestamp (не локальний час!)

    Крок 3: select_related('note__user')
      → traversal через дві FK: reminder → note → user
      → Django генерує: JOIN hello_app_note note ON reminder.note_id = note.id
                       JOIN auth_user u ON note.user_id = u.id
      → Доступ без додаткових запитів: reminder.note.user.email

    SQL:
      SELECT reminder.*, note.*, u.*
      FROM hello_app_reminder reminder
      INNER JOIN hello_app_note note ON reminder.note_id = note.id
      INNER JOIN auth_user u ON note.user_id = u.id
      WHERE reminder.is_sent = FALSE
        AND reminder.remind_at <= NOW()

    Returns:
        QuerySet[Reminder] з prefetched note та note.user
    """
    return Reminder.objects.filter(
        is_sent=False,                      # не відправлені ще
        remind_at__lte=timezone.now()       # час прийшов (remind_at <= зараз)
    ).select_related(
        'note__user'  # подвійний traversal: reminder.note.user.email
    )
