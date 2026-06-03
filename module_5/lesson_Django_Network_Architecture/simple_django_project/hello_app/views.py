from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

from .models import Note              # ← імпортуємо модель


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