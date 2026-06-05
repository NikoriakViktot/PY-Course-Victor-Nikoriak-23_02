from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from asgiref.sync import sync_to_async  # Допомагає виконувати синхронні функції асинхронно
from .models import Note, Category

# Оскільки стандартний декоратор @login_required синхронний, ми адаптуємо його для асинхронних views
from django.utils.decorators import classonlymethod
from django.contrib.auth.mixins import LoginRequiredMixin


# 1. Асинхронна головна сторінка
async def notes_index(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Використовуємо асинхронний фільтр та перетворюємо QuerySet на список асинхронно
    notes_queryset = Note.objects.filter(author=request.user).select_related('category')
    notes_from_db = await sync_to_async(list)(notes_queryset)

    return render(request, 'notes/index.html', {'notes': notes_from_db})


# 2. Асинхронна форма створення нової нотатки
async def note_create(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == "POST":
        title = request.POST.get('title')
        text = request.POST.get('text')
        reminder = request.POST.get('reminder') or None
        category_id = request.POST.get('category')

        category = await Category.objects.aget(id=category_id) if category_id else None

        # Асинхронне створення запису в БД (acreate)
        await Note.objects.acreate(
            title=title,
            text=text,
            reminder=reminder,
            category=category,
            author=request.user
        )
        return redirect('notes_index')

    # Асинхронно дістаємо категорії
    categories_queryset = Category.objects.all()
    categories = await sync_to_async(list)(categories_queryset)
    return render(request, 'notes/Notes.html', {'categories': categories})


# 3. Асинхронне Редагування
async def note_detail(request, note_id):
    if not request.user.is_authenticated:
        return redirect('login')

    # Асинхронне отримання об'єкта (aget)
    note = await Note.objects.aget(id=note_id, author=request.user)

    if request.method == "POST":
        note.title = request.POST.get('title')
        note.text = request.POST.get('text')
        note.reminder = request.POST.get('reminder') or None

        category_id = request.POST.get('category')
        note.category = await Category.objects.aget(id=category_id) if category_id else None

        await sync_to_async(note.save)()
        return redirect('notes_index')

    categories_queryset = Category.objects.all()
    categories = await sync_to_async(list)(categories_queryset)
    return render(request, 'notes/note_detail.html', {'note': note, 'categories': categories})


# 4. Асинхронне Видалення
async def note_delete(request, note_id):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == "POST":
        note = await Note.objects.aget(id=note_id, author=request.user)
        await sync_to_async(note.delete)()
    return redirect('notes_index')


# 5. Функція виходу
async def logout_view(request):
    await sync_to_async(logout)(request)
    return redirect('login')