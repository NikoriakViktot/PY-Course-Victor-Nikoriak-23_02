import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

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


def note_to_dict(note):
    return {
        "id": note.id,
        "title": note.title,
        "text": note.text,
        "reminder": note.reminder.isoformat() if note.reminder else None,
        "category": {
            "id": note.category.id,
            "title": note.category.title,
        },
    }


def notes_api_list(request):
    notes = Note.objects.select_related("category").order_by("id")
    return JsonResponse({"notes": [note_to_dict(note) for note in notes]})


def note_api_detail(request, pk):
    note = get_object_or_404(Note.objects.select_related("category"), pk=pk)
    return JsonResponse(note_to_dict(note))


def get_json_data(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def get_note_data_from_request(request):
    data = get_json_data(request)

    if data is None:
        return None, JsonResponse({"error": "Invalid JSON"}, status=400)

    required_fields = ["title", "text", "category_id"]
    for field in required_fields:
        if field not in data:
            return None, JsonResponse({"error": f"Field '{field}' is required"}, status=400)

    try:
        category = Category.objects.get(pk=data["category_id"])
    except Category.DoesNotExist:
        return None, JsonResponse({"error": "Category was not found"}, status=404)

    reminder = data.get("reminder")
    if reminder:
        reminder = parse_datetime(reminder)
        if reminder is None:
            return None, JsonResponse({"error": "Invalid reminder format"}, status=400)

    return {
        "title": data["title"],
        "text": data["text"],
        "reminder": reminder,
        "category": category,
    }, None


@csrf_exempt
def note_api_create(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method is allowed"}, status=405)

    note_data, error_response = get_note_data_from_request(request)
    if error_response:
        return error_response

    note = Note.objects.create(**note_data)
    return JsonResponse(note_to_dict(note), status=201)


@csrf_exempt
def note_api_update(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method is allowed"}, status=405)

    note = get_object_or_404(Note, pk=pk)
    note_data, error_response = get_note_data_from_request(request)
    if error_response:
        return error_response

    note.title = note_data["title"]
    note.text = note_data["text"]
    note.reminder = note_data["reminder"]
    note.category = note_data["category"]
    note.save()

    return JsonResponse(note_to_dict(note))
