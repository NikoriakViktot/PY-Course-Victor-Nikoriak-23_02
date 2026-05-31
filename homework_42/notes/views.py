import json

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .forms import CategoryForm, NoteFilterForm, NoteForm, DATETIME_LOCAL_FORMAT
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


def categories_list(request):
    categories = Category.objects.prefetch_related("notes")
    return render(request, "notes/categories_list.html", {"categories": categories})


def category_create(request):
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


def note_to_dict(note):
    return {
        "id": note.id,
        "title": note.title,
        "text": note.text,
        "category": note.category_id,
        "category_title": note.category.title,
        "reminder": note.reminder.isoformat() if note.reminder else None,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
    }


def get_json_payload(request):
    if not request.body:
        return {}

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return None

    return payload if isinstance(payload, dict) else None


def form_errors_to_dict(form):
    return {
        field: [str(error) for error in errors] for field, errors in form.errors.items()
    }


def build_note_form_data(payload, note=None):
    data = {}

    for field in ("title", "text", "reminder", "category"):
        if field in payload:
            data[field] = payload[field] if payload[field] is not None else ""
        elif note is not None:
            value = getattr(note, field)
            if field == "category":
                value = note.category_id
            elif field == "reminder" and value is not None:
                value = value.strftime(DATETIME_LOCAL_FORMAT)
            data[field] = value or ""

    return data


@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_notes(request):
    if request.method == "GET":
        notes = Note.objects.select_related("category").all()
        return JsonResponse({"notes": [note_to_dict(note) for note in notes]})

    payload = get_json_payload(request)
    if payload is None:
        return JsonResponse({"errors": {"json": ["Invalid JSON payload."]}}, status=400)

    form = NoteForm(build_note_form_data(payload))
    if not form.is_valid():
        return JsonResponse({"errors": form_errors_to_dict(form)}, status=400)

    note = form.save()
    return JsonResponse({"note": note_to_dict(note)}, status=201)


@csrf_exempt
@require_http_methods(["GET", "PATCH","PUT", "POST"])
def api_note_detail(request, note_id):
    note = get_object_or_404(Note.objects.select_related("category"), id=note_id)

    if request.method == "GET":
        return JsonResponse({"note": note_to_dict(note)})

    payload = get_json_payload(request)
    if payload is None:
        return JsonResponse({"errors": {"json": ["Invalid JSON payload."]}}, status=400)

    form = NoteForm(build_note_form_data(payload, note=note), instance=note)
    if not form.is_valid():
        return JsonResponse({"errors": form_errors_to_dict(form)}, status=400)

    note = form.save()
    return JsonResponse({"note": note_to_dict(note)})