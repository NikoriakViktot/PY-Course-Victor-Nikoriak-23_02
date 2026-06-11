from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import NoteForm, RegisterForm
from .models import Category, Note


class UserLoginView(LoginView):
    template_name = "notes/login.html"


class UserLogoutView(LogoutView):
    pass


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("notes_list")
    else:
        form = RegisterForm()

    return render(request, "notes/register.html", {"form": form})


def user_can_view_note(user, note):
    if note.owner == user:
        return True

    if note.group and note.group in user.groups.all():
        return True

    return False


def user_can_edit_note(user, note):
    return note.owner == user


def filter_notes(request, notes):
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

    return notes


@login_required
def notes_list(request):
    view_mode = request.GET.get("view", "personal")
    categories = Category.objects.order_by("title")
    user_groups = request.user.groups.order_by("name")

    if view_mode == "group":
        notes = Note.objects.select_related("category", "owner", "group").filter(group__in=user_groups)
    else:
        view_mode = "personal"
        notes = Note.objects.select_related("category", "owner", "group").filter(
            owner=request.user,
            group__isnull=True,
        )

    notes = filter_notes(request, notes).order_by("reminder", "title")

    context = {
        "notes": notes,
        "categories": categories,
        "user_groups": user_groups,
        "view_mode": view_mode,
        "selected_category": request.GET.get("category", ""),
        "selected_reminder": request.GET.get("reminder", ""),
    }
    return render(request, "notes/index.html", context)


@login_required
def note_create(request):
    if request.method == "POST":
        form = NoteForm(request.POST, user=request.user)
        if form.is_valid():
            note = form.save(commit=False)
            note.owner = request.user
            selected_group = form.cleaned_data.get("group")

            if selected_group and selected_group not in request.user.groups.all():
                return HttpResponseForbidden("You cannot create notes for this group")

            note.group = selected_group
            note.save()
            return redirect("notes_list")
    else:
        form = NoteForm(user=request.user)

    return render(request, "notes/note_form.html", {"form": form, "title": "Create note"})


@login_required
def note_detail(request, pk):
    note = get_object_or_404(Note.objects.select_related("category", "owner", "group"), pk=pk)

    if not user_can_view_note(request.user, note):
        return HttpResponseForbidden("You do not have access to this note")

    can_edit = user_can_edit_note(request.user, note)

    if request.method == "POST":
        if not can_edit:
            return HttpResponseForbidden("Only the owner can edit this note")

        form = NoteForm(request.POST, instance=note, user=request.user)
        if form.is_valid():
            updated_note = form.save(commit=False)
            selected_group = form.cleaned_data.get("group")

            if selected_group and selected_group not in request.user.groups.all():
                return HttpResponseForbidden("You cannot move notes to this group")

            updated_note.owner = request.user
            updated_note.group = selected_group
            updated_note.save()
            return redirect("note_detail", pk=note.pk)
    else:
        form = NoteForm(instance=note, user=request.user)

    return render(
        request,
        "notes/note_detail.html",
        {
            "note": note,
            "form": form,
            "can_edit": can_edit,
        },
    )


@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk)

    if not user_can_edit_note(request.user, note):
        return HttpResponseForbidden("Only the owner can delete this note")

    if request.method == "POST":
        note.delete()
        return redirect("notes_list")

    return redirect("note_detail", pk=note.pk)
