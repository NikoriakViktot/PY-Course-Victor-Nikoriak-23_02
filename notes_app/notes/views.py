from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Note, Category
from .forms import NoteForm
def main_page(request):
    # Отримуємо параметри пошуку та фільтрації з URL
    search_query = request.GET.get('search', '').strip().lower()
    category_id = request.GET.get('category', '')
    time_filter = request.GET.get('time', '')
    # Базовий запит
    notes = Note.objects.select_related('category').all()
    # Extra: Пошук за title (без урахування регістру)
    if search_query:
        notes = notes.filter(title__icontains=search_query)
    # Extra: Фільтрація за категорією
    if category_id:
        notes = notes.filter(category_id=category_id)
    # Extra: Фільтрація за часом нагадування
    if time_filter == 'upcoming':
        notes = notes.filter(reminder__gt=timezone.now())
    elif time_filter == 'past':
        notes = notes.filter(reminder__lte=timezone.now())
    # Форма для швидкого створення нотатки прямо на головній
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main_page')
    else:
        form = NoteForm()
    categories = Category.objects.all()
    context = {
        'notes': notes,
        'form': form,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_time': time_filter,
    }
    return render(request, 'index.html', context)
def note_detail(request, note_id):
    # Вікно деталей, редагування та видалення
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        # Якщо натиснуто кнопку видалення
        if 'delete' in request.POST:
            note.delete()
            return redirect('main_page')
        # Якщо надіслано форму редагування
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect('note_detail', note_id=note.id)
    else:
        form = NoteForm(instance=note)
    return render(request, 'note_detail.html', {'note': note, 'form': form})