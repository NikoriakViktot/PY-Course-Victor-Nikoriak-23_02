import asyncio
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from asgiref.sync import sync_to_async, async_to_sync
from .models import Note, Category
from .forms import NoteForm
# Оскільки декоратор @login_required синхронний, для асинхронних views
# краще робити перевірку всередині або використовувати асинхронні міMiddlewares.
# Нижче наведено чистий асинхронний view з ручною перевіркою або без неї для тесту продуктивності.
async def main_page(request):
    # (Опціонально) Перевірка авторизації в асинхронному стилі
    if not request.user.is_authenticated:
        return redirect('login_page')
    scope = request.GET.get('scope', 'personal')
    search_query = request.GET.get('search', '').strip().lower()
    category_id = request.GET.get('category', '')
    # Імітація важкої операції або зовнішнього API-запиту (наприклад, перевірка погоди чи курсу валют)
    # Звичайний time.sleep(0.1) заблокував би весь сервер. Асинхронний sleep звільняє потік!
    await asyncio.sleep(0.1)
    # Асинхронне отримання категорій
    # Оскільки QuerySet лінивий, ми обгортаємо виконання запиту в sync_to_async
    get_categories = sync_to_async(lambda: list(Category.objects.all()))
    categories = await get_categories()
    # Асинхронна фільтрація нотаток
    def get_filtered_notes():
        if scope == 'group':
            user_groups = request.user.note_groups.all()
            queryset = Note.objects.filter(group__in=user_groups).select_related('category', 'user', 'group')
        else:
            queryset = Note.objects.filter(user=request.user, group__isnull=True).select_related('category')
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return list(queryset)
    # Виконуємо запит до БД в асинхронному контексті
    notes = await sync_to_async(get_filtered_notes)()
    # Обробка форми (синхронна логіка форми переноситься через фабрику або через sync_to_async)
    if request.method == 'POST':
        # Для простоти прикладу, обробку POST можна залишити синхронною
        # або обгорнути збереження форми, але GET запити є основними для асинхронності
        def handle_post():
            form = NoteForm(request.POST, user=request.user)
            if form.is_valid():
                note = form.save(commit=False)
                note.user = request.user
                note.save()
                return True
            return False
        success = await sync_to_async(handle_post)()
        if success:
            return redirect('main_page')
        form = NoteForm(user=request.user)
    else:
        # Створення форми
        form_init = sync_to_async(lambda: NoteForm(user=request.user))
        form = await form_init()
    context = {
        'notes': notes,
        'form': form,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'current_scope': scope,
    }
    # render у Django є синхронним, тому запускаємо його через sync_to_async
    render_template = sync_to_async(render)
    return await render_template(request, 'index.html', context)
