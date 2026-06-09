from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from .models import Note, Category, NoteGroup
from .forms import NoteForm
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('main_page')
    else:
        form = UserCreationForm()
    return render(request, 'auth.html', {'form': form, 'type': 'register'})
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('main_page')
    else:
        form = AuthenticationForm()
    return render(request, 'auth.html', {'form': form, 'type': 'login'})
def logout_view(request):
    logout(request)
    return redirect('login_page')
@login_required(login_url='login_page')
def main_page(request):
    # Отримуємо тип контенту (персональний чи груповий) з GET-параметру
    scope = request.GET.get('scope', 'personal')
    search_query = request.GET.get('search', '').strip().lower()
    category_id = request.GET.get('category', '')
    # Базова фільтрація: або власні нотатки, або нотатки груп користувача
    if scope == 'group':
        user_groups = request.user.note_groups.all()
        notes = Note.objects.filter(group__in=user_groups).select_related('category', 'user', 'group')
    else:
        notes = Note.objects.filter(user=request.user, group__isnull=True).select_related('category')
    # Пошук та фільтрація за категоріями
    if search_query:
        notes = notes.filter(title__icontains=search_query)
    if category_id:
        notes = notes.filter(category_id=category_id)
    # Обробка створення нотатки
    if request.method == 'POST':
        form = NoteForm(request.POST, user=request.user)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user  # Прив'язуємо поточного користувача
            note.save()
            return redirect('main_page')
    else:
        form = NoteForm(user=request.user)
    categories = Category.objects.all()
    context = {
        'notes': notes,
        'form': form,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'current_scope': scope,
    }
    return render(request, 'index.html', context)
@login_required(login_url='login_page')
def note_detail(request, note_id):
    # Перевіряємо, чи має користувач доступ до нотатки (автор або учасник групи)
    user_groups = request.user.note_groups.all()
    note = get_object_or_404(
        Note.objects.filter(models.Q(user=request.user) | models.Q(group__in=user_groups)),
        id=note_id
    )
    if request.method == 'POST':
        if 'delete' in request.POST:
            # Тільки автор може видалити нотатку
            if note.user == request.user:
                note.delete()
            return redirect('main_page')
        # Редагувати може будь-хто, хто має доступ (наприклад, учасник групи)
        form = NoteForm(request.POST, instance=note, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('note_detail', note_id=note.id)
    else:
        form = NoteForm(instance=note, user=request.user)
    return render(request, 'note_detail.html', {'note': note, 'form': form})