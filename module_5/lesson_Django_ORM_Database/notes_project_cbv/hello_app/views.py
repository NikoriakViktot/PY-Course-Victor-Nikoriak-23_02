"""
views.py — CBV (Class-Based Views) версія

════════════════════════════════════════════════════════════════════
ЦЕЙ ФАЙЛ — навчальна конверсія FBV → CBV.
Порівняй з notes_project/hello_app/views.py (FBV оригінал).
Selectors/Services архітектура ПОВНІСТЮ збережена.
════════════════════════════════════════════════════════════════════

АРХІТЕКТУРА CBV:

  1. View-клас успадковує Generic View:
       ListView / DetailView / CreateView / UpdateView / DeleteView

  2. LoginRequiredMixin — перший у MRO (Python Method Resolution Order)
       MRO: клас → міксини ліворуч → Generic View праворуч
       LoginRequiredMixin.dispatch() перевіряє автентифікацію ПЕРШИМ.

  3. dispatch() — точка входу будь-якого CBV:
       dispatch(request) → роутить на get() / post() / put() ...
       Generic Views реалізують get()/post() — ти тільки перевизначаєш хуки.

  4. Ключові хуки Generic Views:
       get_queryset()      → яку колекцію об'єктів повертати
       get_object()        → який один об'єкт завантажити (Detail/Update/Delete)
       get_context_data()  → які дані передати у шаблон
       get_form_kwargs()   → які аргументи передати у Form.__init__()
       form_valid()        → що робити після успішної валідації
       get_success_url()   → куди редіректити після form_valid()

  5. UserQuerySetMixin — кастомний міксин для ізоляції даних:
       Замість дублювати .filter(user=self.request.user) у кожному класі
       → оголошуємо один раз і підмішуємо.

════════════════════════════════════════════════════════════════════
FBV → CBV QUICK COMPARISON:
════════════════════════════════════════════════════════════════════

  FBV:                               CBV:
  ─────────────────────────────────  ──────────────────────────────
  @login_required                    LoginRequiredMixin (перший!)
  def note_list(request):            class NoteListView(LoginRequiredMixin, ListView):
      notes = selectors.get(...)         model = Note
      return render(req, tmpl, ctx)      template_name = '...'
                                         def get_queryset(self): ...
                                         def get_context_data(self): ...

  def note_create(request):         class NoteCreateView(..., CreateView):
      if request.method == 'POST':       model = Note
          form = NoteForm(POST, user=)   form_class = NoteForm
          if form.is_valid():            def get_form_kwargs(self): ...  # передаємо user=
              services.create_note(...)  def form_valid(self, form): ... # викликаємо service
              redirect(...)

════════════════════════════════════════════════════════════════════
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import NoteForm, NotebookForm, TagForm
from .models import Note, Notebook, Tag
from . import selectors, services


# ─────────────────────────────────────────────────────────────────────────────
# ПУБЛІЧНІ СТОРІНКИ
# ─────────────────────────────────────────────────────────────────────────────

class IndexView(View):
    """
    Головна сторінка — найпростіший CBV.

    View (base class) → потрібно реалізувати get() вручну.
    Без Generic View немає автоматичного render.

    В urls.py: path('', IndexView.as_view(), name='index')
    as_view() → повертає звичайну функцію-callable для Django router.
    """
    def get(self, request):
        return HttpResponse("Hello, Django ORM!")


class AboutView(View):
    def get(self, request):
        return HttpResponse(
            "Notes Project CBV — Class-Based Views версія"
        )


# ─────────────────────────────────────────────────────────────────────────────
# СПІЛЬНИЙ МІКСИН ДЛЯ ІЗОЛЯЦІЇ ДАНИХ
# ─────────────────────────────────────────────────────────────────────────────

class UserQuerySetMixin:
    """
    Міксин для автоматичної фільтрації QuerySet по поточному юзеру.

    Підмішується до Detail/Update/Delete View де потрібно переконатись
    що юзер не може отримати доступ до об'єктів інших юзерів.

    ────────────────────────────────────────────────────────────────
    МРО (Method Resolution Order):
      class NoteDetailView(LoginRequiredMixin, UserQuerySetMixin, DetailView):

      Python MRO: NoteDetailView → LoginRequiredMixin → UserQuerySetMixin → DetailView

      Коли викликається get_queryset():
        → Python шукає метод по ланцюжку MRO
        → Знаходить UserQuerySetMixin.get_queryset()
        → super().get_queryset() → іде далі → DetailView.get_queryset()
        → DetailView повертає self.model.objects.all()
        → UserQuerySetMixin додає .filter(user=self.request.user)

    ────────────────────────────────────────────────────────────────
    БЕЗПЕКА:
      get_queryset() + get_object() у Detail/Update/Delete:
        → DetailView.get_object() робить .get(pk=pk) НА ВІДФІЛЬТРОВАНОМУ QuerySet
        → SQL: SELECT WHERE id=pk AND user_id=<current_user_id>
        → 404 якщо чужий об'єкт → Alice не бачить нотатки Bob'а!
    """
    def get_queryset(self):
        # super().get_queryset() → повертає model.objects.all()
        # .filter(user=...) → обмежуємо тільки об'єктами цього юзера
        return super().get_queryset().filter(user=self.request.user)


# ─────────────────────────────────────────────────────────────────────────────
# NOTE VIEWS
# ─────────────────────────────────────────────────────────────────────────────

class NoteListView(LoginRequiredMixin, ListView):
    """
    Список нотаток з пошуком і фільтрацією.

    ────────────────────────────────────────────────────────────────
    ListView автоматично:
      1. Викликає get_queryset() → отримує список об'єктів
      2. Передає у шаблон як context_object_name (за замовчуванням 'object_list')
      3. Рендерить template_name

    МИ перевизначаємо:
      get_queryset()     → щоб фільтрувати по user + search/tag/notebook
      get_context_data() → щоб додати sidebar дані (notebooks, tags, search)

    ────────────────────────────────────────────────────────────────
    ЗВЕРНИ УВАГУ: у FBV параметри з GET читались прямо у функції.
    У CBV — у get_queryset() та get_context_data() через self.request.GET.
    ────────────────────────────────────────────────────────────────
    """
    model = Note
    template_name = 'hello_app/note_list.html'
    context_object_name = 'notes'  # ім'я змінної у шаблоні (замість object_list)

    def _get_filters(self):
        """
        Парсить GET параметри один раз і зберігає в self.
        Викликається і з get_queryset() і з get_context_data().
        """
        if hasattr(self, '_filters_parsed'):
            return
        self._filters_parsed = True

        # Пошуковий рядок
        self.search = self.request.GET.get('q', '').strip()

        # Тег за id (перевірка прав!)
        tag_id = self.request.GET.get('tag')
        self.active_tag = None
        if tag_id:
            try:
                self.active_tag = Tag.objects.get(id=int(tag_id), user=self.request.user)
            except (Tag.DoesNotExist, ValueError):
                pass  # некоректний id → ігноруємо

        # Записник за id (перевірка прав!)
        notebook_id = self.request.GET.get('notebook')
        self.active_notebook = None
        if notebook_id:
            try:
                self.active_notebook = Notebook.objects.get(id=int(notebook_id), user=self.request.user)
            except (Notebook.DoesNotExist, ValueError):
                pass

    def get_queryset(self):
        """
        Делегуємо у selectors.get_user_notes() — архітектура збережена!

        FBV еквівалент:
          notes = selectors.get_user_notes(request.user, search=..., tag=..., notebook=...)
        """
        self._get_filters()
        return selectors.get_user_notes(
            self.request.user,
            search=self.search or None,
            tag=self.active_tag,
            notebook=self.active_notebook,
        )

    def get_context_data(self, **kwargs):
        """
        Додаємо sidebar дані до автоматичного контексту ListView.

        super().get_context_data() вже містить:
          context['notes']      → результат get_queryset()
          context['page_obj']   → якщо є пагінація
          context['is_paginated'] → boolean
        """
        self._get_filters()
        ctx = super().get_context_data(**kwargs)
        ctx['notebooks'] = selectors.get_user_notebooks(self.request.user)
        ctx['tags'] = selectors.get_user_tags(self.request.user)
        ctx['search'] = self.search
        ctx['active_tag'] = self.active_tag
        ctx['active_notebook'] = self.active_notebook
        return ctx


class NoteDetailView(LoginRequiredMixin, UserQuerySetMixin, DetailView):
    """
    Деталь однієї нотатки.

    ────────────────────────────────────────────────────────────────
    DetailView автоматично:
      1. Читає pk з URL kwargs
      2. Викликає get_object() → get_queryset().get(pk=pk)
      3. Передає як 'object' або context_object_name у шаблон
      4. 404 якщо не знайдено

    UserQuerySetMixin.get_queryset() → фільтрує по user=self.request.user
    → SQL: SELECT WHERE id=pk AND user_id=<current_user>
    → Alice не може побачити нотатку Bob'а → 404 замість 403 (security through obscurity)

    ────────────────────────────────────────────────────────────────
    У FBV ми використовували selector:
      selectors.get_note_detail(request.user, pk)
    У CBV — get_object() перевизначаємо щоб використати selector з Prefetch.
    ────────────────────────────────────────────────────────────────
    """
    model = Note
    template_name = 'hello_app/note_detail.html'
    context_object_name = 'note'

    def get_object(self, queryset=None):
        """
        Використовуємо selector для завантаження з Prefetch(to_attr=...).
        FBV: selectors.get_note_detail(request.user, pk)
        """
        try:
            return selectors.get_note_detail(self.request.user, self.kwargs['pk'])
        except Note.DoesNotExist:
            raise Http404("Нотатку не знайдено")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # upcoming_reminders встановлений через Prefetch(to_attr=) у selector
        ctx['reminders'] = getattr(self.object, 'upcoming_reminders', [])
        return ctx


class NoteCreateView(LoginRequiredMixin, CreateView):
    """
    Створення нотатки.

    ────────────────────────────────────────────────────────────────
    CreateView автоматично:
      GET:
        1. Ініціалізує порожню форму form_class()
        2. Рендерить template_name з {'form': form}
      POST:
        1. Ініціалізує форму з request.POST → form_class(request.POST)
        2. form.is_valid() → True: form_valid(form) | False: form_invalid(form)

    МИ перевизначаємо:
      get_form_kwargs() → додаємо user= бо NoteForm.__init__ потребує його
      form_valid()      → викликаємо services.create_note() замість form.save()
                          (зберігаємо Services/Selectors архітектуру!)

    ────────────────────────────────────────────────────────────────
    ЧОМУ get_form_kwargs() а не просто form_class(request.POST, user=...)?

    CreateView будує форму у get_form():
      def get_form(self):
          return self.form_class(**self.get_form_kwargs())

    get_form_kwargs() повертає:
      {'data': request.POST, 'files': request.FILES, 'initial': ...}

    Ми додаємо: kwargs['user'] = self.request.user
    → форма отримає NoteForm(data=POST, user=request.user) — саме те що потрібно!
    ────────────────────────────────────────────────────────────────
    """
    model = Note
    form_class = NoteForm
    template_name = 'hello_app/note_form.html'

    def get_form_kwargs(self):
        """
        Передаємо user= у NoteForm для фільтрації queryset FK/M:N полів.

        FBV: form = NoteForm(request.POST, user=request.user)
        CBV: get_form_kwargs() додає user= до kwargs → CreateView передасть у form
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Створити'
        ctx['title'] = 'Нова нотатка'
        return ctx

    def form_valid(self, form):
        """
        Замість form.save() → викликаємо services.create_note().
        Services архітектура: transaction.atomic() залишається у service!

        FBV еквівалент:
          if form.is_valid():
              note = services.create_note(user=..., title=..., ...)
              messages.success(...)
              return redirect(...)

        form_valid() = обробка успішної валідації у CBV.
        НЕ викликаємо super().form_valid() — там буде form.save() якого ми не хочемо.
        """
        tags = form.cleaned_data.get('tags')
        tag_ids = [t.id for t in tags] if tags else None

        note = services.create_note(
            user=self.request.user,
            title=form.cleaned_data['title'],
            content=form.cleaned_data.get('content', ''),
            priority=form.cleaned_data.get('priority', 1),
            notebook=form.cleaned_data.get('notebook'),
            tag_ids=tag_ids,
        )
        messages.success(self.request, f'✅ Нотатку "{note.title}" створено!')
        return redirect('hello_app:note_detail', pk=note.pk)


class NoteUpdateView(LoginRequiredMixin, UserQuerySetMixin, UpdateView):
    """
    Редагування нотатки.

    ────────────────────────────────────────────────────────────────
    UpdateView автоматично:
      GET:
        1. get_object() → завантажує існуючий об'єкт (з get_queryset!)
        2. Ініціалізує форму з instance=object → автозаповнення полів
        3. Рендерить шаблон
      POST:
        1. get_object() → завантажує об'єкт
        2. Ініціалізує форму з instance=object, data=POST
        3. form.is_valid() → True: form_valid() | False: form_invalid()

    UserQuerySetMixin.get_queryset() → .filter(user=self.request.user)
    → get_object() звертається до відфільтрованого queryset → 404 якщо чужий!

    FBV:
      note = get_object_or_404(Note, pk=pk, user=request.user)
      form = NoteForm(request.POST, instance=note, user=request.user)
    CBV:
      UserQuerySetMixin → безпека
      get_form_kwargs() → додаємо user=
      UpdateView → автоматично instance=object
    ────────────────────────────────────────────────────────────────
    """
    model = Note
    form_class = NoteForm
    template_name = 'hello_app/note_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['note'] = self.object  # для breadcrumbs у шаблоні
        ctx['action'] = 'Зберегти зміни'
        ctx['title'] = f'Редагувати: {self.object.title}'
        return ctx

    def form_valid(self, form):
        """
        Делегуємо у services.update_note() — НЕ form.save().

        tag_ids=[] (порожній список) = "видалити всі теги"
        tag_ids=None = "не змінювати теги" (різна семантика!)
        """
        tags = form.cleaned_data.get('tags')
        tag_ids = [t.id for t in tags] if tags else []

        note = self.get_object()
        services.update_note(
            note,
            title=form.cleaned_data['title'],
            content=form.cleaned_data.get('content', ''),
            priority=form.cleaned_data.get('priority', note.priority),
            notebook=form.cleaned_data.get('notebook'),
            is_pinned=form.cleaned_data.get('is_pinned', note.is_pinned),
            tag_ids=tag_ids,
        )
        messages.success(self.request, f'✅ Нотатку "{note.title}" оновлено!')
        return redirect('hello_app:note_detail', pk=note.pk)


class NoteDeleteView(LoginRequiredMixin, UserQuerySetMixin, DeleteView):
    """
    Видалення нотатки.

    ────────────────────────────────────────────────────────────────
    DeleteView автоматично:
      GET:  рендерить шаблон підтвердження (note_confirm_delete.html)
      POST: викликає form_valid()

    МИ перевизначаємо form_valid() щоб:
      1. Зберегти title до видалення (після delete → недоступний)
      2. Викликати services.delete_note() замість object.delete()
      3. Показати messages.warning
      4. Редіректити на список

    UserQuerySetMixin → 404 якщо чужа нотатка.

    Чому ТІЛЬКИ POST для видалення?
      GET видалення = порушення HTTP семантики:
        → браузерний prefetch може видалити!
        → пошуковий бот може відвідати посилання і видалити!
      DeleteView автоматично вимагає POST для видалення — правильно!
    ────────────────────────────────────────────────────────────────
    """
    model = Note
    template_name = 'hello_app/note_confirm_delete.html'
    success_url = reverse_lazy('hello_app:note_list')
    context_object_name = 'note'

    def form_valid(self, form):
        """
        Хук що викликається при POST (підтвердження видалення).
        FBV: if request.method == 'POST': services.delete_note(note)
        """
        note = self.get_object()
        title = note.title  # зберігаємо до видалення!
        services.delete_note(note)
        messages.warning(self.request, f'🗑️ Нотатку "{title}" видалено.')
        return redirect(self.success_url)


# ─────────────────────────────────────────────────────────────────────────────
# NOTEBOOK VIEWS
# ─────────────────────────────────────────────────────────────────────────────

class NotebookListView(LoginRequiredMixin, ListView):
    """
    Список записників поточного користувача.

    get_queryset() використовує selector що вже додає annotate(note_count).
    """
    model = Notebook
    template_name = 'hello_app/notebook_list.html'
    context_object_name = 'notebooks'

    def get_queryset(self):
        return selectors.get_user_notebooks(self.request.user)


class NotebookCreateView(LoginRequiredMixin, CreateView):
    """
    Створення записника.

    NotebookForm не потребує user= у __init__ (немає FK/M:N queryset).
    user= передається тільки в services.create_notebook().
    """
    model = Notebook
    form_class = NotebookForm
    template_name = 'hello_app/notebook_form.html'
    success_url = reverse_lazy('hello_app:notebook_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новий записник'
        ctx['action'] = 'Створити'
        return ctx

    def form_valid(self, form):
        notebook = services.create_notebook(
            user=self.request.user,
            title=form.cleaned_data['title'],
            color=form.cleaned_data.get('color', '#4A90E2'),
            is_default=form.cleaned_data.get('is_default', False),
        )
        if form.cleaned_data.get('description'):
            notebook.description = form.cleaned_data['description']
            notebook.save(update_fields=['description'])
        messages.success(self.request, f'Записник "{notebook.title}" створено!')
        return redirect(self.success_url)


class NotebookUpdateView(LoginRequiredMixin, UserQuerySetMixin, UpdateView):
    """
    Редагування записника.
    UserQuerySetMixin → get_object() поверне 404 якщо чужий записник.
    """
    model = Notebook
    form_class = NotebookForm
    template_name = 'hello_app/notebook_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['notebook'] = self.object
        ctx['title'] = f'Редагувати: {self.object.title}'
        ctx['action'] = 'Зберегти'
        return ctx

    def form_valid(self, form):
        notebook = self.get_object()
        services.update_notebook(
            notebook,
            title=form.cleaned_data['title'],
            description=form.cleaned_data.get('description', ''),
            color=form.cleaned_data.get('color', '#4A90E2'),
            is_default=form.cleaned_data.get('is_default', False),
        )
        messages.success(self.request, f'Записник "{notebook.title}" оновлено!')
        return redirect('hello_app:notebook_list')


class NotebookDeleteView(LoginRequiredMixin, UserQuerySetMixin, DeleteView):
    """
    Видалення записника.

    on_delete=SET_NULL у Note.notebook FK → нотатки НЕ видаляються!
    Зберігаємо note_count до видалення щоб показати у повідомленні.
    """
    model = Notebook
    template_name = 'hello_app/notebook_confirm_delete.html'
    success_url = reverse_lazy('hello_app:notebook_list')
    context_object_name = 'notebook'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['note_count'] = self.object.notes.count()
        return ctx

    def form_valid(self, form):
        notebook = self.get_object()
        title = notebook.title
        note_count = notebook.notes.count()
        services.delete_notebook(notebook)
        messages.warning(
            self.request,
            f'Записник "{title}" видалено. {note_count} нотаток стали без записника.'
        )
        return redirect(self.success_url)


# ─────────────────────────────────────────────────────────────────────────────
# TAG VIEWS
# ─────────────────────────────────────────────────────────────────────────────

class TagCreateView(LoginRequiredMixin, CreateView):
    """
    Створення нового тегу з підтримкою ?next= URL параметра.

    ────────────────────────────────────────────────────────────────
    Особливість: підтримує ?next=<url> для повернення після створення.
    Наприклад: /tags/new/?next=/notes/new/
      → після створення тегу повертається на форму нотатки.

    get_success_url() читає next з GET або POST.
    Якщо next відсутній → повертається на note_create за замовчуванням.

    Також підтримує ?name=python → initial value для поля name.
    ────────────────────────────────────────────────────────────────
    """
    model = Tag
    form_class = TagForm
    template_name = 'hello_app/tag_form.html'

    def get_initial(self):
        """
        Передаємо initial значення у форму.
        FBV: initial = {}; if request.GET.get('name'): initial['name'] = ...
        """
        initial = super().get_initial()
        name = self.request.GET.get('name')
        if name:
            initial['name'] = name
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новий тег'
        ctx['action'] = 'Створити'
        # next передаємо в шаблон щоб зберегти у hidden input форми
        ctx['next'] = self._get_next_url()
        return ctx

    def _get_next_url(self):
        """Повертає URL для redirect після збереження."""
        return (
            self.request.GET.get('next')
            or self.request.POST.get('next')
            or 'hello_app:note_create'
        )

    def get_success_url(self):
        return self._get_next_url()

    def form_valid(self, form):
        """
        create_or_get_tag() повертає (tag, created):
          created=True  → 'Тег створено'
          created=False → 'Тег вже існує'

        Після збереження — redirect на next_url (PRG патерн).
        """
        tag, created = services.create_or_get_tag(
            user=self.request.user,
            name=form.cleaned_data['name'],
            color=form.cleaned_data.get('color', '#808080'),
        )
        if created:
            messages.success(self.request, f'✅ Тег "#{tag.name}" створено!')
        else:
            messages.info(self.request, f'ℹ️ Тег "#{tag.name}" вже існує.')

        next_url = self._get_next_url()
        return redirect(next_url)
