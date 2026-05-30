from django.shortcuts import get_object_or_404, redirect, render
from .forms import NoteFilterForm, NoteForm
from .models import Note


def notes_list(request):
    notes = Note.objects.select_related('category').all().order_by('-id')
    filter_form = NoteFilterForm(request.GET or None)

    if filter_form.is_valid():
        query = filter_form.cleaned_data.get('query')
        category = filter_form.cleaned_data.get('category')
        reminder_from = filter_form.cleaned_data.get('reminder_from')
        reminder_to = filter_form.cleaned_data.get('reminder_to')

        if query:
            notes = notes.filter(title__icontains=query)
        if category:
            notes = notes.filter(category=category)
        if reminder_from:
            notes = notes.filter(reminder__gte=reminder_from)
        if reminder_to:
            notes = notes.filter(reminder__lte=reminder_to)

    context = {'notes': notes, 'filter_form': filter_form}
    return render(request, 'notes/index.html', context)


def note_create(request):
    form = NoteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('notes_list')

    return render(request, 'notes/note_form.html', {'form': form, 'is_create': True})


def note_detail(request, note_id):
    note = get_object_or_404(Note.objects.select_related('category'), id=note_id)
    form = NoteForm(request.POST or None, instance=note)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('note_detail', note_id=note.id)

    return render(request, 'notes/note_detail.html', {'note': note, 'form': form})


def note_delete(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        note.delete()
        return redirect('notes_list')
    return redirect('note_detail', note_id=note_id)