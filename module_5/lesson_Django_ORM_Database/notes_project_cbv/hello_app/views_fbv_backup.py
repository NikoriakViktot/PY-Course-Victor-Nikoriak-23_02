"""
views_fbv_backup.py — FBV (Function-Based Views) оригінал

════════════════════════════════════════════════════════════════════
ЦЕЙ ФАЙЛ — резервна копія для порівняння FBV ↔ CBV.
НЕ підключений до urls.py. Django його не виконує.

Оригінал: notes_project/hello_app/views.py
CBV версія: views.py (цей самий проект, переписаний на класи)

Як читати:
  Кожна функція має блок "CBV еквівалент" у docstring.
  Відкрий views.py поруч і порівнюй відповідний клас.
════════════════════════════════════════════════════════════════════
"""

"""
views.py — HTTP шар (тільки request/response!)

════════════════════════════════════════════════════════════════════
РОЛЬ VIEW В АРХІТЕКТУРІ:
════════════════════════════════════════════════════════════════════

View — це функція що:
  1. Отримує HTTP request
  2. Парсить параметри (GET, POST, URL kwargs)
  3. Делегує читання → selectors.py (SELECT запити)
  4. Делегує зміни  → services.py  (INSERT/UPDATE/DELETE)
  5. Повертає HTTP response (render або redirect)

View НЕ повинен:
  ✗ Писати QuerySets (Note.objects.filter...)
  ✗ Містити бізнес-логіку
  ✗ Знати про транзакції, select_related тощо

Чому такий поділ?
  View = обробник HTTP → тільки HTTP концепції
  Selector = "як отримати ці дані" → тільки ORM концепції
  Service = "бізнес-правила" → тільки логіка

  Якщо логіка тільки в View → неможливо використати з API або Celery.
  Якщо логіка в Services → однаковий код для View, API, Celery!

════════════════════════════════════════════════════════════════════
@login_required — декоратор автентифікації
════════════════════════════════════════════════════════════════════

  @login_required
  def note_list(request):
      ...

  Якщо user НЕ залогінений:
    → redirect до settings.LOGIN_URL (зазвичай '/accounts/login/')
    → ?next=/notes/ (щоб після логіну повернутись на цю сторінку)

  Якщо user залогінений:
    → виконується view функція нормально

════════════════════════════════════════════════════════════════════
PRG ПАТЕРН (Post/Redirect/Get):
════════════════════════════════════════════════════════════════════

  БЕЗ REDIRECT:
    POST /notes/create/ → 200 OK (HTML)
    F5 → "Повторити відправку форми?" → дублікат нотатки!

  З REDIRECT:
    POST /notes/create/ → 302 Redirect → GET /notes/42/
    F5 → GET /notes/42/ → безпечно, немає дублікату!

  Правило: після успішного POST завжди return redirect(...)!

════════════════════════════════════════════════════════════════════
Безпека — ізоляція даних:
════════════════════════════════════════════════════════════════════

  # ПРАВИЛЬНО: get_object_or_404 з user=request.user
  note = get_object_or_404(Note, pk=pk, user=request.user)
  # Якщо Alice намагається GET /notes/99/ де 99 — нотатка Bob'а:
  # → SELECT WHERE id=99 AND user_id=<alice.id> → не знайдено → 404

  # НЕПРАВИЛЬНО: без user перевірки
  note = get_object_or_404(Note, pk=pk)
  # → Alice може бачити будь-яку нотатку за id!
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404

from .models import Note, Tag, Notebook
from .forms import NoteForm, NotebookForm, TagForm
from . import selectors, services


# ─────────────────────────────────────────────────────────────────────────────
# ПУБЛІЧНІ СТОРІНКИ (без @login_required)
# ─────────────────────────────────────────────────────────────────────────────

def index(request):
    """
    Головна сторінка.

    Найпростіший View — рендер статичного шаблону або HttpResponse.
    request.user: залогінений → User instance, незалогінений → AnonymousUser

    ════════════════════════════════════════════════════════════════
    CBV еквівалент: class IndexView(View)
      Базовий View (не Generic!) — потрібно реалізувати get() вручну.
      TemplateView рендерить шаблон автоматично, але для HttpResponse
      достатньо базового View.
    ════════════════════════════════════════════════════════════════
    """
    return HttpResponse("Hello, Django ORM!")


def about(request):
    """
    Сторінка 'Про проект'.

    ════════════════════════════════════════════════════════════════
    CBV еквівалент: class AboutView(View)
      Так само як IndexView — базовий View з get() вручну.
      Альтернатива: TemplateView з template_name='about.html' якщо є шаблон.
    ════════════════════════════════════════════════════════════════
    """
    return HttpResponse(
        "Notes Project — демонстрація Django ORM та Services/Selectors архітектури"
    )


# ─────────────────────────────────────────────────────────────────────────────
# NOTE VIEWS (всі захищені @login_required)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def note_list(request):
    """
    Список нотаток поточного користувача з фільтрацією.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЕЙ VIEW (покроково):
    ════════════════════════════════════════════════════════════════

    Крок 1: Читаємо параметри фільтрації з URL
      GET /notes/?q=python&notebook=3&tag=7
      request.GET — QueryDict: {'q': ['python'], 'notebook': ['3'], 'tag': ['7']}
      request.GET.get('q', '') → 'python' або '' якщо відсутній

      .strip() → видаляємо пробіли: "  python  " → "python"
      Порожній рядок після strip = немає пошуку

    Крок 2: Конвертуємо notebook_id та tag_id
      request.GET.get('notebook') → рядок '3' або None
      Нам потрібен Notebook instance для filter(notebook=notebook)
      → Завантажуємо з БД + перевіряємо права доступу (user=request.user)

      try/except: захист від:
        - notebook_id='abc' → ValueError при int('abc')
        - notebook не існує або чужий → DoesNotExist
      В обох випадках: notebook = None (ігноруємо некоректний параметр)

    Крок 3: Делегуємо читання даних selector'у
      View НЕ знає як побудувати QuerySet — це завдання selectors.py!
      selectors.get_user_notes(user, search=..., tag=..., notebook=...)
      → повертає ЛІНИВИЙ QuerySet (SQL ще не виконано!)

    Крок 4: render() → шаблон виконає ітерацію QuerySet → SQL виконається тут!
      render() → templates/hello_app/note_list.html
      {% for note in notes %} → ось тут Django виконує SQL SELECT

    ════════════════════════════════════════════════════════════════
    КОНТЕКСТ ШАБЛОНУ:
    ════════════════════════════════════════════════════════════════
      notes      → QuerySet нотаток (з select_related та prefetch від selector)
      notebooks  → QuerySet записників (з note_count annotate)
      tags       → QuerySet тегів (з note_count annotate)
      search     → поточний пошуковий запит (для відображення у input)
      active_tag      → активний тег фільтру (для підсвічення у sidebar)
      active_notebook → активний записник (для підсвічення у sidebar)

    ════════════════════════════════════════════════════════════════
    CBV еквівалент: NoteListView(LoginRequiredMixin, ListView)
      @login_required           → LoginRequiredMixin (перший у MRO!)
      Читання GET params прямо  → _get_filters() + self.request.GET
                                   у get_queryset() та get_context_data()
      selectors.get_user_notes  → get_queryset() делегує у selector
      render(request, tmpl, ctx)→ ListView рендерить автоматично;
                                   ctx будується у get_context_data()
    ════════════════════════════════════════════════════════════════
    """
    # ── Крок 1: Читаємо GET параметри ───────────────────────────────────────
    search = request.GET.get('q', '').strip()
    tag_id = request.GET.get('tag')
    notebook_id = request.GET.get('notebook')

    # ── Крок 2: Завантажуємо entities по id (з перевіркою прав) ─────────────
    tag = None
    if tag_id:
        try:
            # get() → перевіряє що тег існує І належить цьому юзеру
            tag = Tag.objects.get(id=int(tag_id), user=request.user)
        except (Tag.DoesNotExist, ValueError):
            pass  # некоректний id → ігноруємо, tag залишається None

    notebook = None
    if notebook_id:
        try:
            notebook = Notebook.objects.get(id=int(notebook_id), user=request.user)
        except (Notebook.DoesNotExist, ValueError):
            pass

    # ── Крок 3: Отримуємо дані через selector (QuerySet ще не виконано!) ────
    notes = selectors.get_user_notes(
        request.user,           # user → фільтр ізоляції даних
        search=search or None,  # '' → None (selector перевіряє if search)
        tag=tag,                # None або Tag instance
        notebook=notebook,      # None або Notebook instance
    )
    # Sidebar дані:
    notebooks = selectors.get_user_notebooks(request.user)  # з note_count
    tags = selectors.get_user_tags(request.user)            # з note_count

    # ── Крок 4: Рендер шаблону (тут QuerySet виконується!) ──────────────────
    return render(request, 'hello_app/note_list.html', {
        'notes': notes,                      # QuerySet → SQL при {% for note in notes %}
        'notebooks': notebooks,
        'tags': tags,
        'search': search,                    # для value="{{ search }}" у шаблоні
        'active_tag': tag,                   # для підсвічення активного фільтру
        'active_notebook': notebook,
    })


@login_required
def note_detail(request, pk):
    """
    Деталь нотатки.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЕЙ VIEW (покроково):
    ════════════════════════════════════════════════════════════════

    Крок 1: Завантажуємо нотатку через selector
      get_note_detail(user, pk) → Note з select_related + Prefetch
      Піднімає Note.DoesNotExist якщо:
        - нотатки з id=pk не існує
        - нотатка існує але належить іншому юзеру

    Крок 2: Перехоплюємо Note.DoesNotExist → Http404
      except Note.DoesNotExist: raise Http404(...)
      → Django відображає 404 сторінку
      → НЕ 500, не AttributeError — коректна HTTP семантика!

    Крок 3: Передаємо нотатку і нагадування у шаблон
      note.upcoming_reminders — встановлено через Prefetch(to_attr=...)
      getattr(note, 'upcoming_reminders', []) — на випадок якщо attr відсутній

    ════════════════════════════════════════════════════════════════
    CBV еквівалент: NoteDetailView(LoginRequiredMixin, UserQuerySetMixin, DetailView)
      get_object_or_404(Note, pk=pk, user=...) → UserQuerySetMixin.get_queryset()
                                                   + DetailView.get_object()
      except DoesNotExist: raise Http404       → те саме, автоматично у get_object()
      render(ctx)                              → get_context_data() + автоматичний render

      Відмінність: у CBV get_object() перевизначається щоб використати
      selectors.get_note_detail() з Prefetch(to_attr=).
    ════════════════════════════════════════════════════════════════

    Args:
        pk: int — Primary Key нотатки (з URL /notes/<int:pk>/)
    """
    # ── Крок 1: Завантаження через selector ──────────────────────────────────
    try:
        note = selectors.get_note_detail(request.user, pk)
        # Всередині selector: .get(id=note_id, user=user)
        # Якщо note чужий → DoesNotExist (не 403 Forbidden — security through obscurity)
    except Note.DoesNotExist:
        # Не показуємо "Заборонено" (дає інформацію зловмиснику що id=99 існує!)
        # Показуємо "Не знайдено" — той самий ефект для легального юзера
        raise Http404("Нотатку не знайдено")

    # ── Крок 2: Рендер ───────────────────────────────────────────────────────
    return render(request, 'hello_app/note_detail.html', {
        'note': note,
        # upcoming_reminders встановлений через Prefetch(to_attr=) у selector
        # getattr: безпечно якщо attr не встановлено (fallback до [])
        'reminders': getattr(note, 'upcoming_reminders', []),
    })


@login_required
def note_create(request):
    """
    Створення нотатки (PRG патерн).

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЕЙ VIEW (покроково):
    ════════════════════════════════════════════════════════════════

    GET запит (відкриття форми):
      Крок 1: if request.method == 'POST': → False → else гілка
      Крок 2: form = NoteForm(user=request.user) → порожня форма
              user= → форма покаже тільки НАШІ записники і теги
      Крок 3: render форми

    POST запит (відправка форми):
      Крок 1: if request.method == 'POST': → True
      Крок 2: form = NoteForm(request.POST, user=request.user)
              request.POST → прив'язуємо дані → форма стає "bound"
              user= → queryset фільтрація для FK/M:N валідації
      Крок 3: form.is_valid()
              → to_python() → validate() → run_validators() → clean_*()
              → True: form.cleaned_data готовий
              → False: form.errors готовий → re-render з помилками

      Крок 4 (якщо is_valid=True):
              Дістаємо tag_ids з M:N поля
              services.create_note(...) → transaction.atomic() → INSERT
              messages.success(...) → Django Messages Framework
              redirect(...) → PRG: 302 Redirect!

      Крок 5 (якщо is_valid=False):
              Не редіректимо! render() з form (що містить errors + введені дані)
              Шаблон: {{ form.title.errors }} → показує помилки поруч з полем
              Введені дані збережені у form.data → відображаються у полях

    ════════════════════════════════════════════════════════════════
    DJANGO MESSAGES FRAMEWORK:
    ════════════════════════════════════════════════════════════════

      messages.success(request, 'Текст') → SUCCESS рівень
      messages.warning(request, 'Текст') → WARNING рівень
      messages.error(request, 'Текст')   → ERROR рівень

      У шаблоні: {% for msg in messages %} {{ msg }} {% endfor %}
      Повідомлення показуються ОДИН РАЗ після redirect, потім зникають.

    ════════════════════════════════════════════════════════════════
    CBV еквівалент: NoteCreateView(LoginRequiredMixin, CreateView)
      if request.method == 'POST': ... else: ...  → автоматично у CreateView
      NoteForm(request.POST, user=request.user)   → get_form_kwargs() додає user=;
                                                     CreateView передає data=POST
      if form.is_valid(): ...                     → CreateView викликає form_valid()
                                                     автоматично при POST
      services.create_note(...)                   → form_valid() хук (НЕ form.save()!)
      render(request, tmpl, {'form': form})       → form_invalid() + автоматичний render
    ════════════════════════════════════════════════════════════════
    """
    if request.method == 'POST':
        # ── Крок 1: Прив'язуємо POST дані до форми ──────────────────────────
        form = NoteForm(
            request.POST,           # сирі дані від браузера (потенційно небезпечні!)
            user=request.user       # для фільтрації notebook/tags queryset
        )

        # ── Крок 2: Валідація (Validation Pipeline) ──────────────────────────
        if form.is_valid():
            # form.cleaned_data тепер існує і містить типізовані Python-об'єкти

            # ── Крок 3: Дістаємо tag_ids із M:N поля ────────────────────────
            # form.cleaned_data['tags'] → QuerySet[Tag] (вже валідований!)
            tags = form.cleaned_data.get('tags')
            # Перетворюємо у list[int] для передачі в service
            tag_ids = [t.id for t in tags] if tags else None

            # ── Крок 4: Створюємо через service ─────────────────────────────
            note = services.create_note(
                user=request.user,                           # автор
                title=form.cleaned_data['title'],            # str (validated)
                content=form.cleaned_data.get('content', ''), # str або ''
                priority=form.cleaned_data.get('priority', 1), # int 1-4
                notebook=form.cleaned_data.get('notebook'),   # Notebook або None
                tag_ids=tag_ids,                             # list[int] або None
            )

            # ── Крок 5: Messages + PRG Redirect ─────────────────────────────
            messages.success(request, f'✅ Нотатку "{note.title}" створено!')
            # PRG: redirect → 302 → GET /notes/42/ → безпека від дублювання!
            return redirect('hello_app:note_detail', pk=note.pk)

        # Якщо is_valid=False → падаємо через до render нижче

    else:
        # ── GET запит: порожня форма ─────────────────────────────────────────
        form = NoteForm(user=request.user)  # порожня, але з queryset по user

    # Рендеримо форму (і при GET і при POST з помилками)
    return render(request, 'hello_app/note_form.html', {
        'form': form,           # contains: fields, errors (якщо POST), initial values
        'action': 'Створити',   # текст кнопки Submit
        'title': 'Нова нотатка', # заголовок сторінки
    })


@login_required
def note_edit(request, pk):
    """
    Редагування нотатки.

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЕЙ VIEW (покроково):
    ════════════════════════════════════════════════════════════════

    Ключова відмінність від note_create:
      1. get_object_or_404(Note, pk=pk, user=request.user)
         → Завантажуємо існуючий об'єкт + перевіряємо права
      2. NoteForm(request.POST, instance=note, ...)
         → instance=note: при save() оновлює існуючий запис, не створює новий
      3. NoteForm(instance=note, ...) при GET
         → форма автоматично заповнюється поточними значеннями!

    Безпека:
      get_object_or_404(Note, pk=pk, user=request.user)
      → SQL: SELECT WHERE id=pk AND user_id=request.user.id
      → 404 якщо не знайдено → Alice не може редагувати нотатки Bob'а!

    ════════════════════════════════════════════════════════════════
    CBV еквівалент: NoteUpdateView(LoginRequiredMixin, UserQuerySetMixin, UpdateView)
      get_object_or_404(Note, pk=pk, user=) → UserQuerySetMixin.get_queryset()
                                               + UpdateView.get_object()
      NoteForm(POST, instance=note, user=)  → UpdateView автоматично передає
                                               instance=self.object; get_form_kwargs()
                                               додає user=
      if form.is_valid(): services.update_note()  → form_valid() хук
      NoteForm(instance=note, user=)        → GET: UpdateView ініціалізує instance=
                                               автоматично → поля заповнені
    ════════════════════════════════════════════════════════════════

    Args:
        pk: int — Primary Key нотатки для редагування
    """
    # ── Завантажуємо нотатку + security check ───────────────────────────────
    # get_object_or_404: SELECT + 404 якщо не знайдено (замість try/except)
    note = get_object_or_404(Note, pk=pk, user=request.user)

    if request.method == 'POST':
        # ── instance=note: форма знає що оновлює, а не створює ──────────────
        form = NoteForm(request.POST, instance=note, user=request.user)

        if form.is_valid():
            # Дістаємо тег id (tag_ids=[] → видалити всі теги!)
            tags = form.cleaned_data.get('tags')
            tag_ids = [t.id for t in tags] if tags else []
            # tag_ids=[] а не None: пустий список = "прибрати всі теги"
            # tag_ids=None = "не змінювати теги" (різна семантика в service!)

            # service.update_note оновлює тільки передані поля (часткове оновлення)
            services.update_note(
                note,                                          # існуючий об'єкт
                title=form.cleaned_data['title'],
                content=form.cleaned_data.get('content', ''),
                priority=form.cleaned_data.get('priority', note.priority),
                notebook=form.cleaned_data.get('notebook'),
                is_pinned=form.cleaned_data.get('is_pinned', note.is_pinned),
                tag_ids=tag_ids,
            )
            messages.success(request, f'✅ Нотатку "{note.title}" оновлено!')
            return redirect('hello_app:note_detail', pk=note.pk)

    else:
        # ── GET запит: форма заповнена поточними значеннями (instance=note) ──
        # instance=note → Django автоматично встановлює initial values з об'єкта!
        # note.title → form.fields['title'].initial = note.title → <input value="...">
        form = NoteForm(instance=note, user=request.user)

    return render(request, 'hello_app/note_form.html', {
        'form': form,
        'note': note,                       # для breadcrumbs у шаблоні
        'action': 'Зберегти зміни',
        'title': f'Редагувати: {note.title}',
    })


@login_required
def note_delete(request, pk):
    """
    Видалення нотатки (тільки через POST!).

    ════════════════════════════════════════════════════════════════
    ЧОМУ НЕ МОЖНА ВИДАЛЯТИ ЧЕРЕЗ GET?
    ════════════════════════════════════════════════════════════════

    HTTP GET семантика: "отримати ресурс" (не змінювати стан!)
    Якщо GET /notes/42/delete/ видаляє нотатку:
      → Браузерний prefetch може випадково видалити!
      → Пошукові боти можуть "відвідати" посилання і видалити!
      → Антивірус/проксі що сканує посилання → видалення!

    Правильно: GET → сторінка підтвердження, POST → видалення

    ════════════════════════════════════════════════════════════════
    ЩО РОБИТЬ ЦЕЙ VIEW (покроково):
    ════════════════════════════════════════════════════════════════

    GET /notes/42/delete/:
      → Завантажуємо нотатку (security check)
      → Рендеримо note_confirm_delete.html
        ("Ти впевнений? Видалиться також N нагадувань" + форма з POST)

    POST /notes/42/delete/:
      → Завантажуємо нотатку (security check)
      → services.delete_note(note) → CASCADE видаляє і нагадування
      → messages.warning + redirect на список

    Шаблон confirm_delete містить:
      <form method="post">
          {% csrf_token %}
          <button type="submit">Видалити назавжди</button>
      </form>
    Натискання → POST до цього ж URL → видалення!

    ════════════════════════════════════════════════════════════════
    CBV еквівалент: NoteDeleteView(LoginRequiredMixin, UserQuerySetMixin, DeleteView)
      get_object_or_404(Note, pk=pk, user=) → UserQuerySetMixin + DeleteView.get_object()
      if request.method == 'POST':          → DeleteView.form_valid() хук (POST)
          services.delete_note(note)        → form_valid() викликає services.delete_note()
          redirect(...)                     → redirect(self.success_url)
      GET render confirm_delete             → автоматично (template_name)
      context_object_name = 'note'         → в шаблоні {{ note }} замість {{ object }}
    ════════════════════════════════════════════════════════════════

    Args:
        pk: int — Primary Key нотатки для видалення
    """
    # Security check: note.user MUST = request.user (або 404!)
    note = get_object_or_404(Note, pk=pk, user=request.user)

    if request.method == 'POST':
        # ── Видаляємо через service ──────────────────────────────────────────
        title = note.title  # зберігаємо title до видалення (після delete → недоступний)
        services.delete_note(note)
        # CASCADE у БД автоматично видалить: Reminder для цієї нотатки
        # Django автоматично очистить: hello_app_note_tags (M:N junction table)

        messages.warning(request, f'🗑️ Нотатку "{title}" видалено.')
        # Redirect на список → PRG патерн
        return redirect('hello_app:note_list')

    # ── GET: сторінка підтвердження ───────────────────────────────────────────
    return render(request, 'hello_app/note_confirm_delete.html', {
        'note': note,
        # note.reminders.count() → в шаблоні показуємо скільки нагадувань видалиться
    })


# ─────────────────────────────────────────────────────────────────────────────
# NOTEBOOK VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def notebook_list(request):
    """
    Список записників поточного користувача.

    selectors.get_user_notebooks() повертає QuerySet з annotate(note_count=Count('notes')).
    Шаблон може показати кількість нотаток без додаткових запитів: {{ notebook.note_count }}.

    ════════════════════════════════════════════════════════════════
    CBV еквівалент: NotebookListView(LoginRequiredMixin, ListView)
      model = Notebook
      context_object_name = 'notebooks'
      get_queryset() → selectors.get_user_notebooks(self.request.user)
    ════════════════════════════════════════════════════════════════
    """
    notebooks = selectors.get_user_notebooks(request.user)
    return render(request, 'hello_app/notebook_list.html', {
        'notebooks': notebooks,
    })


@login_required
def notebook_create(request):
    """
    Створення нового записника (PRG патерн).

    GET → порожня форма NotebookForm
    POST → валідація → services.create_notebook() → redirect на notebook_list

    NotebookForm не потребує user= у __init__ (немає FK/M:N queryset),
    але user передається в services.create_notebook(user=request.user).

    Зверни увагу: description оновлюється окремим save() після create_notebook()
    бо create_notebook() не приймає description як аргумент — обмеження service API.

    ════════════════════════════════════════════════════════════════
    CBV еквівалент: NotebookCreateView(LoginRequiredMixin, CreateView)
      if request.method == 'POST': ... else:  → автоматично у CreateView
      NotebookForm НЕ потребує get_form_kwargs() — user= не у __init__
      form_valid()  → services.create_notebook(); окремий save(description)
      success_url = reverse_lazy('hello_app:notebook_list')
    ════════════════════════════════════════════════════════════════
    """
    if request.method == 'POST':
        form = NotebookForm(request.POST)
        if form.is_valid():
            notebook = services.create_notebook(
                user=request.user,
                title=form.cleaned_data['title'],
                color=form.cleaned_data.get('color', '#4A90E2'),
                is_default=form.cleaned_data.get('is_default', False),
            )
            # Оновлюємо description окремо — create_notebook не приймає description
            if form.cleaned_data.get('description'):
                notebook.description = form.cleaned_data['description']
                notebook.save(update_fields=['description'])
            messages.success(request, f'Записник "{notebook.title}" створено!')
            return redirect('hello_app:notebook_list')
    else:
        form = NotebookForm()

    return render(request, 'hello_app/notebook_form.html', {
        'form': form,
        'title': 'Новий записник',
        'action': 'Створити',
    })


@login_required
def notebook_edit(request, pk):
    """
    Редагування записника.

    GET:  завантажуємо notebook, рендеримо форму з instance=notebook (автозаповнення)
    POST: валідуємо, викликаємо services.update_notebook(), redirect

    Безпека:
      get_object_or_404(Notebook, pk=pk, user=request.user)
      → SQL: SELECT WHERE id=pk AND user_id=alice.id
      → 404 якщо чужий записник

    NotebookForm не потребує user= у __init__ (немає FK/M:N queryset).

    ════════════════════════════════════════════════════════════════
    CBV еквівалент: NotebookUpdateView(LoginRequiredMixin, UserQuerySetMixin, UpdateView)
      get_object_or_404(Notebook, pk=pk, user=) → UserQuerySetMixin + UpdateView.get_object()
      NotebookForm(POST, instance=notebook)     → UpdateView автоматично instance=
      if form.is_valid(): services.update_note()→ form_valid() хук
    ════════════════════════════════════════════════════════════════

    Args:
        pk: int — Primary Key записника для редагування
    """
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
            return redirect('hello_app:notebook_list')
    else:
        form = NotebookForm(instance=notebook)

    return render(request, 'hello_app/notebook_form.html', {
        'form': form,
        'notebook': notebook,
        'title': f'Редагувати: {notebook.title}',
        'action': 'Зберегти',
    })


@login_required
def notebook_delete(request, pk):
    """
    Видалення записника (тільки POST, GET показує підтвердження).

    GET: рендерить підтвердження з кількістю нотаток що стануть без записника.
    POST: видаляє записник через service.

    Важливо — on_delete=SET_NULL у Note.notebook FK:
      → При видаленні Notebook: нотатки НЕ видаляються!
      → note.notebook_id → NULL (нотатки стають "без записника")
      → note_count показуємо у шаблоні щоб попередити юзера

    ════════════════════════════════════════════════════════════════
    CBV еквівалент: NotebookDeleteView(LoginRequiredMixin, UserQuerySetMixin, DeleteView)
      get_object_or_404(Notebook, pk=pk, user=) → UserQuerySetMixin + DeleteView.get_object()
      GET render confirm                        → автоматично (template_name)
      if request.method == 'POST':              → DeleteView.form_valid() хук
          note_count = notebook.notes.count()  → get_context_data() для GET;
                                                  form_valid() для POST
          services.delete_notebook(notebook)   → form_valid()
      success_url = reverse_lazy('hello_app:notebook_list')
    ════════════════════════════════════════════════════════════════

    Args:
        pk: int — Primary Key записника для видалення
    """
    notebook = get_object_or_404(Notebook, pk=pk, user=request.user)

    if request.method == 'POST':
        title = notebook.title
        note_count = notebook.notes.count()
        services.delete_notebook(notebook)
        messages.warning(
            request,
            f'Записник "{title}" видалено. {note_count} нотаток стали без записника.'
        )
        return redirect('hello_app:notebook_list')

    return render(request, 'hello_app/notebook_confirm_delete.html', {
        'notebook': notebook,
        'note_count': notebook.notes.count(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# TAG VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def tag_create(request):
    """
    Створення нового тегу (PRG патерн).

    GET  -> порожня форма TagForm
    POST -> create_or_get_tag() -> redirect

    Підтримує параметр ?next=<url> для повернення після створення.
    Наприклад: /tags/new/?next=/notes/new/ -> після створення повернутись
    на форму нотатки.

    create_or_get_tag() повертає (tag, created):
      - created=True  -> новий тег (повідомлення 'Тег створено')
      - created=False -> тег вже існував (повідомлення 'Тег вже існує')

    Параметри URL:
      ?next=<url>   — куди редіректити після збереження
                      Зберігається у hidden input форми → передається у POST
      ?name=python  — попередньо заповнює поле name

    ════════════════════════════════════════════════════════════════
    CBV еквівалент: TagCreateView(LoginRequiredMixin, CreateView)
      next_url = GET.get('next') or POST.get('next') or ...
                                  → get_success_url() читає _get_next_url()
      if request.method == 'POST':→ автоматично у CreateView
      initial = {'name': ...}     → get_initial() повертає {'name': GET.get('name')}
      if form.is_valid():
          services.create_or_get_tag()  → form_valid() хук
          redirect(next_url)           → return redirect(self._get_next_url())
    ════════════════════════════════════════════════════════════════
    """
    # URL для повернення після збереження (default: note_create)
    next_url = request.GET.get('next') or request.POST.get('next') or 'hello_app:note_create'

    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag, created = services.create_or_get_tag(
                user=request.user,
                name=form.cleaned_data['name'],   # вже нормалізовано clean_name()
                color=form.cleaned_data.get('color', '#808080'),
            )
            if created:
                messages.success(request, f'✅ Тег "#{tag.name}" створено!')
            else:
                messages.info(request, f'ℹ️ Тег "#{tag.name}" вже існує.')

            return redirect(next_url)
    else:
        # GET: порожня форма (можна передати initial name з URL ?name=python)
        initial = {}
        if request.GET.get('name'):
            initial['name'] = request.GET.get('name')
        form = TagForm(initial=initial)

    return render(request, 'hello_app/tag_form.html', {
        'form': form,
        'title': 'Новий тег',
        'action': 'Створити',
        'next': next_url,
    })
