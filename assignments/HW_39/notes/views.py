from django.shortcuts import render, get_object_or_404, redirect
from .models import Note, Category


# 1. Головна сторінка (Виведення списку нотаток)
def notes_index(request):
    notes_from_db = Note.objects.all().select_related('category')
    return render(request, 'notes/index.html', {'notes': notes_from_db})


# 2. Форма створення нової нотатки
def note_create(request):
    if request.method == "POST":
        title = request.POST.get('title')
        text = request.POST.get('text')
        reminder = request.POST.get('reminder') or None
        category_id = request.POST.get('category')

        category = Category.objects.get(id=category_id) if category_id else None

        # Створюємо запис у базі даних
        Note.objects.create(
            title=title,
            text=text,
            reminder=reminder,
            category=category
        )
        # ПІСЛЯ ЗБЕРЕЖЕННЯ: повертаємось на головне вікно (борд)
        return redirect('notes_index')

    categories = Category.objects.all()
    # Рендеримо твій файл Notes.html з великої літери N
    return render(request, 'notes/Notes.html', {'categories': categories})


# 3. Детальний перегляд та Редагування нотатки
def note_detail(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    if request.method == "POST":
        note.title = request.POST.get('title')
        note.text = request.POST.get('text')
        note.reminder = request.POST.get('reminder') or None

        category_id = request.POST.get('category')
        note.category = Category.objects.get(id=category_id) if category_id else None

        note.save()
        return redirect('notes_index')

    categories = Category.objects.all()
    return render(request, 'notes/note_detail.html', {'note': note, 'categories': categories})


# 4. Видалення нотатки
def note_delete(request, note_id):
    if request.method == "POST":
        note = get_object_or_404(Note, id=note_id)
        note.delete()
    return redirect('notes_index')