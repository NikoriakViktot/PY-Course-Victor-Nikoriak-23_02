from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages   # ← Django Messages

# Create your views here.
from django.http import HttpResponse

from .models import Note              # ← імпортуємо модель
from .forms import NoteForm           # ← наша форма


def index(request):
    """Головна сторінка — повертає просте текстове повідомлення."""
    return HttpResponse("Hello, Django!")


def about(request):
    """Сторінка 'Про нас'."""
    return HttpResponse("Це моя перша сторінка на Django!")

def note_list(request):
    """
    Сторінка зі списком нотаток.

    Що відбувається:
    1. Note.objects.all() — робить SELECT * FROM hello_app_note ORDER BY created_at DESC
       (порядок DESC заданий в class Meta: ordering = ['-created_at'])
    2. render() — бере шаблон, підставляє дані (context) і повертає HTML
    """

    # ORM запит: отримати всі нотатки з БД
    # Результат — QuerySet: лінивий список об'єктів Note
    notes = Note.objects.all()

    # context — словник даних які передаємо в шаблон
    # Ключ 'notes' → в шаблоні: {{ notes }}, {% for note in notes %}
    context = {
        'notes': notes,
    }

    # render(request, 'шлях/до/шаблону', context)
    # Django шукає шаблон в hello_app/templates/hello_app/note_list.html
    return render(request, 'hello_app/note_list.html', context)

def note_detail(request, pk):
    """
    Деталь нотатки.
    get_object_or_404: якщо note з цим pk не існує → повертає 404 (не 500).
    Теорія: DJANGO_TEMPLATES_BOOTSTRAP.md §6 — HttpRequest/Response.
    """
    note = get_object_or_404(Note, pk=pk)
    return render(request, 'hello_app/note_detail.html', {'note': note})


def note_create(request):
    """
    PRG (Post/Redirect/Get) паттерн:
    GET  → показати порожню форму
    POST → обробити, зберегти → redirect на список (щоб F5 не дублював)
    Без redirect: F5 після POST повторить збереження → дублікат нотатки.
    Теорія: DJANGO_TEMPLATES_BOOTSTRAP.md §8 — PRG Pattern.
    """
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save()
            # Django Message — flash-повідомлення відображається після redirect
            messages.success(request, f'Нотатку "{note.title}" успішно створено!')
            return redirect('hello_app:note_list')
    else:
        form = NoteForm()

    return render(request, 'hello_app/note_form.html', {
        'form': form,
        'action': 'Створити',
        'title': 'Нова нотатка',
    })


def note_edit(request, pk):
    """Редагування нотатки — та само PRG, але форма ініціалізована instance=note."""
    note = get_object_or_404(Note, pk=pk)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, f'Нотатку "{note.title}" оновлено!')
            return redirect('hello_app:note_detail', pk=note.pk)
    else:
        form = NoteForm(instance=note)  # instance заповнює форму поточними даними

    return render(request, 'hello_app/note_form.html', {
        'form': form,
        'note': note,
        'action': 'Зберегти зміни',
        'title': f'Редагувати: {note.title}',
    })


def note_delete(request, pk):
    """
    Видалення через POST (не GET!).
    GET → сторінка підтвердження.
    POST → видалити → redirect.
    Ніколи не видаляти через GET — це небезпечно (CSRF, prefetch).
    Теорія: DJANGO_TEMPLATES_BOOTSTRAP.md §8 — Security, CSRF.
    """
    note = get_object_or_404(Note, pk=pk)

    if request.method == 'POST':
        title = note.title
        note.delete()
        messages.warning(request, f'Нотатку "{title}" видалено.')
        return redirect('hello_app:note_list')

    return render(request, 'hello_app/note_confirm_delete.html', {'note': note})