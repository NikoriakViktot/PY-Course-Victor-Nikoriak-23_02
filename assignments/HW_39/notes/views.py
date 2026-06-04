from django.shortcuts import render
from .models import Note


def notes_index(request):
    notes_from_db = Note.objects.all().select_related('category')

    return render(request, 'notes/index.html', {'notes': notes_from_db})