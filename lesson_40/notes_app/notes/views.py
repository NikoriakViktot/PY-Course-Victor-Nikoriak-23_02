from django.shortcuts import render

from .models import Note


def notes_list(request):
    notes = Note.objects.select_related("category").order_by("reminder", "title")
    return render(request, "notes/index.html", {"notes": notes})
