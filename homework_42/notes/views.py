import json

from asgiref.sync import sync_to_async
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .forms import CategoryForm, DATETIME_LOCAL_FORMAT, NoteFilterForm, NoteForm
from .models import Category, Note
from .telegram import publish_created_note

ALLOWED_ORDERINGS = {"-created_at", "created_at", "reminder", "category__title"}
NOTE_SCOPE_GROUP = "group"
NOTE_SCOPE_PERSONAL = "personal"


def get_user_group_ids(user):
    return user.groups.values_list("id", flat=True)


def accessible_notes_for_user(user):
    return Note.objects.select_related("category", "owner", "group").filter(
        Q(owner=user) | Q(group_id__in=get_user_group_ids(user))
    )


def scoped_notes_for_user(user, scope):
    notes = Note.objects.select_related("category", "owner", "group")
    if scope == NOTE_SCOPE_GROUP:
        return notes.filter(group_id__in=get_user_group_ids(user))
    return notes.filter(owner=user, group__isnull=True)


@login_required
def _sync_notes_list(request):
    scope = request.GET.get("scope", NOTE_SCOPE_PERSONAL)
    if scope not in {NOTE_SCOPE_PERSONAL, NOTE_SCOPE_GROUP}:
        scope = NOTE_SCOPE_PERSONAL

    notes = scoped_notes_for_user(request.user, scope)
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

    context = {
        "notes": notes,
        "filter_form": filter_form,
        "scope": scope,
        "personal_scope": NOTE_SCOPE_PERSONAL,
        "group_scope": NOTE_SCOPE_GROUP,
    }
    return render(request, "notes/index.html", context)


@login_required
def _sync_note_create(request):
    form = NoteForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        note = form.save(commit=False)
        note.owner = request.user
        note.save()
        telegram_result = publish_created_note(note)
        if telegram_result.sent:
            messages.success(request, "Нотатку створено та надіслано в Telegram канал.")
        elif telegram_result.skipped:
            messages.warning(
                request,
                "Нотатку створено, але Telegram не налаштовано: "
                f"{telegram_result.reason}",
            )
        else:
            messages.warning(
                request,
                "Нотатку створено, але не вдалося надіслати в Telegram: "
                f"{telegram_result.reason}",
            )
        return redirect(note)

    return render(request, "notes/note_form.html", {"form": form, "is_create": True})


@login_required
def _sync_note_detail(request, note_id):
    note = get_object_or_404(accessible_notes_for_user(request.user), id=note_id)
    can_edit = note.owner_id == request.user.id

    if request.method == "POST" and not can_edit:
        return HttpResponseForbidden(
            "Групові нотатки інших користувачів доступні лише для перегляду."
        )

    form = NoteForm(request.POST or None, instance=note, user=request.user)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Нотатку оновлено.")
        return redirect(note)

    return render(
        request,
        "notes/note_detail.html",
        {"note": note, "form": form, "can_edit": can_edit},
    )


@login_required
def _sync_note_delete(request, note_id):
    note = get_object_or_404(Note, id=note_id, owner=request.user)
    if request.method == "POST":
        note.delete()
        messages.success(request, "Нотатку видалено.")
        return redirect("notes_list")
    return redirect("note_detail", note_id=note_id)


@login_required
def _sync_categories_list(request):
    categories = Category.objects.prefetch_related("notes")
    return render(request, "notes/categories_list.html", {"categories": categories})


@login_required
def _sync_category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Категорію створено.")
        return redirect("categories_list")

    return render(
        request, "notes/category_form.html", {"form": form, "is_create": True}
    )


@login_required
def _sync_category_update(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    form = CategoryForm(request.POST or None, instance=category)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Категорію оновлено.")
        return redirect("categories_list")

    return render(
        request, "notes/category_form.html", {"form": form, "category": category}
    )


@login_required
def _sync_category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Категорію видалено разом із її нотатками.")
        return redirect("categories_list")
    return redirect("categories_list")


@require_POST
def _sync_logout_view(request):
    logout(request)
    messages.success(request, "Ви вийшли з системи.")
    return redirect("login")


async def run_sync_view(view_func, request, *args, **kwargs):
    return await sync_to_async(view_func, thread_sensitive=True)(
        request, *args, **kwargs
    )


@login_required
async def notes_list(request):
    return await run_sync_view(_sync_notes_list, request)


@login_required
async def note_create(request):
    return await run_sync_view(_sync_note_create, request)


@login_required
async def note_detail(request, note_id):
    return await run_sync_view(_sync_note_detail, request, note_id)


@login_required
async def note_delete(request, note_id):
    return await run_sync_view(_sync_note_delete, request, note_id)


@login_required
async def categories_list(request):
    return await run_sync_view(_sync_categories_list, request)


@login_required
async def categories_create(request):
    return await run_sync_view(_sync_category_create, request)


@login_required
async def category_create(request):
    return await run_sync_view(_sync_category_create, request)


@login_required
async def categories_update(request, category_id):
    return await run_sync_view(_sync_category_update, request, category_id)


@login_required
async def category_update(request, category_id):
    return await run_sync_view(_sync_category_update, request, category_id)


@login_required
async def categories_delete(request, category_id):
    return await run_sync_view(_sync_category_delete, request, category_id)


@login_required
async def category_delete(request, category_id):
    return await run_sync_view(_sync_category_delete, request, category_id)


@login_required
async def logout_view(request):
    return await run_sync_view(_sync_logout_view, request)


def note_to_dict(note):
    return {
        "id": note.id,
        "title": note.title,
        "text": note.text,
        "category": note.category_id,
        "category_title": note.category.title,
        "owner": note.owner_id,
        "owner_username": note.owner.username if note.owner else None,
        "group": note.group_id,
        "group_name": note.group.name if note.group else None,
        "reminder": note.reminder.isoformat() if note.reminder else None,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
        "telegram_sent_at": (
            note.telegram_sent_at.isoformat() if note.telegram_sent_at else None
        ),
        "reminder_telegram_sent_at": (
            note.reminder_telegram_sent_at.isoformat()
            if note.reminder_telegram_sent_at
            else None
        ),
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

    for field in ("title", "text", "reminder", "category", "group"):
        if field in payload:
            data[field] = payload[field] if payload[field] is not None else ""
        elif note is not None:
            value = getattr(note, field)
            if field == "category":
                value = note.category_id
            elif field == "group":
                value = note.group_id
            elif field == "reminder" and value is not None:
                value = value.strftime(DATETIME_LOCAL_FORMAT)
            data[field] = value or ""

    return data


@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
def _sync_api_notes(request):
    if request.method == "GET":
        scope = request.GET.get("scope", NOTE_SCOPE_PERSONAL)
        if scope not in {NOTE_SCOPE_PERSONAL, NOTE_SCOPE_GROUP}:
            scope = NOTE_SCOPE_PERSONAL
        notes = scoped_notes_for_user(request.user, scope)
        return JsonResponse({"notes": [note_to_dict(note) for note in notes]})

    payload = get_json_payload(request)
    if payload is None:
        return JsonResponse({"errors": {"json": ["Invalid JSON payload."]}}, status=400)

    form = NoteForm(build_note_form_data(payload), user=request.user)
    if not form.is_valid():
        return JsonResponse({"errors": form_errors_to_dict(form)}, status=400)

    note = form.save(commit=False)
    note.owner = request.user
    note.save()
    telegram_result = publish_created_note(note)
    response_data = {"note": note_to_dict(note)}
    response_data["telegram"] = {
        "sent": telegram_result.sent,
        "skipped": telegram_result.skipped,
        "reason": telegram_result.reason,
    }
    return JsonResponse(response_data, status=201)


@csrf_exempt
@login_required
@require_http_methods(["GET", "PATCH", "PUT", "POST"])
def _sync_api_note_detail(request, note_id):
    note = get_object_or_404(accessible_notes_for_user(request.user), id=note_id)

    if request.method == "GET":
        return JsonResponse({"note": note_to_dict(note)})

    if note.owner_id != request.user.id:
        return JsonResponse(
            {
                "errors": {
                    "permission": ["Group notes owned by another user are read-only."]
                }
            },
            status=403,
        )

    payload = get_json_payload(request)
    if payload is None:
        return JsonResponse({"errors": {"json": ["Invalid JSON payload."]}}, status=400)

    form = NoteForm(
        build_note_form_data(payload, note=note), instance=note, user=request.user
    )
    if not form.is_valid():
        return JsonResponse({"errors": form_errors_to_dict(form)}, status=400)

    note = form.save()
    return JsonResponse({"note": note_to_dict(note)})


@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
async def api_notes(request):
    return await run_sync_view(_sync_api_notes, request)


@csrf_exempt
@login_required
@require_http_methods(["GET", "PATCH", "PUT", "POST"])
async def api_note_detail(request, note_id):
    return await run_sync_view(_sync_api_note_detail, request, note_id)


__all__ = [
    "api_note_detail",
    "api_notes",
    "categories_list",
    "category_create",
    "categories_create",
    "category_delete",
    "category_update",
    "note_create",
    "note_delete",
    "note_detail",
    "notes_list",
    "logout_view",
]