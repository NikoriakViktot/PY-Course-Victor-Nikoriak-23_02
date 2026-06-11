from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import NoteForm
from .models import Category, Note


def notes_list(request):
    notes = Note.objects.select_related("category").order_by("reminder", "title")
    categories = Category.objects.order_by("title")

    category_id = request.GET.get("category")
    reminder_filter = request.GET.get("reminder")

    if category_id:
        notes = notes.filter(category_id=category_id)

    if reminder_filter == "with_reminder":
        notes = notes.filter(reminder__isnull=False)
    elif reminder_filter == "without_reminder":
        notes = notes.filter(reminder__isnull=True)
    elif reminder_filter == "today":
        today = timezone.localdate()
        notes = notes.filter(reminder__date=today)

    context = {
        "notes": notes,
        "categories": categories,
        "selected_category": category_id,
        "selected_reminder": reminder_filter,
    }
    return render(request, "notes/index.html", context)


def note_create(request):
    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("notes_list")
    else:
        form = NoteForm()

    return render(request, "notes/note_form.html", {"form": form, "title": "Create note"})


def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk)

    if request.method == "POST":
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect("note_detail", pk=note.pk)
    else:
        form = NoteForm(instance=note)

    return render(request, "notes/note_detail.html", {"note": note, "form": form})


def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk)

    if request.method == "POST":
        note.delete()
        return redirect("notes_list")

    return redirect("note_detail", pk=note.pk)
