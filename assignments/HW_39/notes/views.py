from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Note, Category


# 1. Головна сторінка (Тільки для своїх нотаток)
@login_required
def notes_index(request):
    # ФІЛЬТРАЦІЯ: Дістаємо нотатки ТОЧНО того користувача, який зараз увійшов (request.user)
    notes_from_db = Note.objects.filter(author=request.user).select_related('category')
    return render(request, 'notes/index.html', {'notes': notes_from_db})


# 2. Форма створення нової нотатки
@login_required
def note_create(request):
    if request.method == "POST":
        title = request.POST.get('title')
        text = request.POST.get('text')
        reminder = request.POST.get('reminder') or None
        category_id = request.POST.get('category')

        category = Category.objects.get(id=category_id) if category_id else None

        # При створенні явно вказуємо поточного користувача як автора
        Note.objects.create(
            title=title,
            text=text,
            reminder=reminder,
            category=category,
            author=request.user
        )
        return redirect('notes_index')

    categories = Category.objects.all()
    return render(request, 'notes/Notes.html', {'categories': categories})


# 3. Детальний перегляд та Редагування (Тільки своєї нотатки)
@login_required
def note_detail(request, note_id):
    # Захист: користувач може отримати нотатку тільки якщо він є її автором
    note = get_object_or_404(Note, id=note_id, author=request.user)

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


# 4. Видалення нотатки (Тільки своєї)
@login_required
def note_delete(request, note_id):
    if request.method == "POST":
        note = get_object_or_404(Note, id=note_id, author=request.user)
        note.delete()
    return redirect('notes_index')


# 5. Функція виходу із системи
def logout_view(request):
    logout(request)
    return redirect('login')