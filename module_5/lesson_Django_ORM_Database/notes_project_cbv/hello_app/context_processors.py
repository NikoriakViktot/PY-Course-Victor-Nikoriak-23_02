"""
context_processors.py — глобальні змінні шаблону

════════════════════════════════════════════════════════════════
ЩО ТАКЕ CONTEXT PROCESSOR?
════════════════════════════════════════════════════════════════

Кожен Context Processor — це функція що:
    1. Отримує поточний request
    2. Повертає dict (змінні додаються до КОЖНОГО шаблону!)

Це ідеальне місце для:
    - Sidebar даних (notebooks, tags)
    - Глобальних лічильників (кількість непрочитаних повідомлень)
    - Конфігурацій що потрібні на всіх сторінках

БЕЗ Context Processor (поганий підхід — дублювання!):
    def note_list(request):
        notebooks = get_user_notebooks(request.user)
        tags = get_user_tags(request.user)
        ...

    def note_detail(request):
        notebooks = get_user_notebooks(request.user)  # дублювання!
        tags = get_user_tags(request.user)             # дублювання!
        ...

З Context Processor (правильно — один раз):
    Sidebar дані автоматично доступні у КОЖНОМУ шаблоні!
    {{ sidebar_notebooks }} → доступний скрізь без явної передачі

════════════════════════════════════════════════════════════════
ЯК ПІДКЛЮЧИТИ:
════════════════════════════════════════════════════════════════

В settings.py у TEMPLATES[0]['OPTIONS']['context_processors']:
    'hello_app.context_processors.sidebar_context',

════════════════════════════════════════════════════════════════
УВАГА: Performance
════════════════════════════════════════════════════════════════

Context processor викликається для КОЖНОГО запиту!
Тому:
    - Завжди використовуй select_related/annotate (не N+1!)
    - Для незалогіненого юзера → повертаємо порожні списки
    - Кешуй якщо дані не змінюються часто (Redis cache)

Поточна реалізація: 2 SQL запити на кожен сторінку (прийнятно).
Оптимізація: Per-request caching через request.session або Django cache.
"""
from .selectors import get_user_notebooks, get_user_tags


def sidebar_context(request):
    """
    Додає дані для бічної панелі до кожного шаблону.

    Повертає:
        sidebar_notebooks — записники поточного юзера з note_count
        sidebar_tags      — теги поточного юзера з note_count

    Обробка незалогіненого юзера:
        request.user.is_authenticated → False → {} (порожній dict)
        Шаблон: {% if sidebar_notebooks %} → False → не показуємо нічого
    """
    # ── Крок 1: Перевіряємо чи є залогінений юзер ───────────────────────────
    if not request.user.is_authenticated:
        # AnonymousUser → не робимо SQL запити, повертаємо порожні значення
        return {
            'sidebar_notebooks': [],
            'sidebar_tags': [],
        }

    # ── Крок 2: Завантажуємо дані через selectors (з annotate → без N+1!) ───
    # Ці QuerySets ЛІНИВІ — SQL виконається лише коли шаблон їх ітерує
    sidebar_notebooks = get_user_notebooks(request.user)
    # SQL (приблизно):
    # SELECT notebook.*, COUNT(note.id) FILTER (WHERE NOT archived) as note_count
    # FROM hello_app_notebook
    # WHERE user_id = <request.user.id>
    # ORDER BY title

    sidebar_tags = get_user_tags(request.user)
    # SQL (приблизно):
    # SELECT tag.*, COUNT(note_tag.note_id) as note_count
    # FROM hello_app_tag
    # LEFT JOIN hello_app_note_tags ON tag.id = note_tag.tag_id
    # WHERE tag.user_id = <request.user.id>
    # ORDER BY name

    # ── Крок 3: Повертаємо dict → автоматично мержиться у кожен template context
    return {
        'sidebar_notebooks': sidebar_notebooks,
        'sidebar_tags': sidebar_tags,
    }
