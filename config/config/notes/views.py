from django.shortcuts import render
from .models import Note

def notes_list(request):
    notes = Note.objects.all().order_by('-created_at')
    return render(request, 'notes/notes_list.html', {'notes': notes})