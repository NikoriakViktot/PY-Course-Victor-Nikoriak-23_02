from django.shortcuts import render
from .models import Note


def notes_list(request):
    notes = Note.objects.all()

    return render(request, 'home.html', {'notes': notes})