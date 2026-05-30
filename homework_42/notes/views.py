from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CategoryForm, NoteFilterForm, NoteForm
from .models import Category, Note

ALLOWED_ORDERINGS = {"-created_at", "created_at", "reminder", "category_title"}


def notes_list(request):
    notes = Note.objects.select_related("category").all()
    filter_form = NoteFilterForm(request.GET or None)

    if filter_form.is_valid():
        query = filter_form.cleaned_data.get("query")
        category = filter_form.cleaned_data.get("category")
        reminder_from = filter_form.cleaned_data.get("reminder_from")
        reminder_to = filter_form.cleaned_data.get("reminder_to")
        ordering = filter_form.cleaned_data.get("ordering") or "-created_at"

        if query:
            notes = notes.filter(Q(title__icontains=query) | Q(text__icontains=query))
        if category:
            notes = notes.filter(category=category)
        if reminder_from:
            notes = notes.filter(reminder__gte=reminder_from)
        if reminder_to:
            notes = notes.filter(reminder__lte=reminder_to)
        if ordering in ALLOWED_ORDERINGS:
            notes = notes.order_by(ordering, "-id")

    context = {"notes": notes, "filter_form": filter_form}
    return render(request, "notes/index.html", context)


def note_create(request):
    form = NoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        note = form.save()
        messages.success(request, "Нотатку створено.")
        return redirect(note)

    return render(request, "notes/note_form.html", {"form": form, "is_create": True})


def note_detail(request, note_id):
    note = get_object_or_404(Note.objects.select_related("category"), id=note_id)
    form = NoteForm(request.POST or None, instance=note)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Нотатку оновлено.")
        return redirect(note)

    return render(request, "notes/note_detail.html", {"note": note, "form": form})


def note_delete(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.method == "POST":
        note.delete()
        messages.success(request, "Нотатку видалено.")
        return redirect("notes_list")
    return redirect("note_detail", note_id=note_id)


def category_list(request):
    categories = Category.objects.prefetch_related("notes")
    return render(request, "notes/categories_list.html", {"categories": categories})


def  category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Категорію створено.")
        return redirect("category_list")

    return render(
        request, "notes/category_form.html", {"form": form, "is_create": True}
    )


def category_update(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    form = CategoryForm(request.POST or None, instance=category)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Категорію оновлено.")
        return redirect("category_list")

    return render(
        request, "notes/category_form.html", {"form": form, "category": category}
    )


def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Категорію видалено разом із її нотатками.")
        return redirect("categories_list")
    return redirect("categories_list")