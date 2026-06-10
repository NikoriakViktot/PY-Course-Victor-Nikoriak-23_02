## 1. Модель даних (`models.py`)

Спочатку створимо структуру для нашої нотатки. Нам потрібні поля для назви, тексту, дедлайну нагадування та категорії.

Python

```
from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Назва категорії")

    def __str__(self):
        return self.name

class Note(models.Model):
    title = models.CharField(max_length=200, verbose_name="Назва")
    text = models.TextField(verbose_name="Текст нотатки")
    reminder = models.DateTimeField(null=True, blank=True, verbose_name="Час нагадування")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категорія")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
```

## 2. Форма (`forms.py`)

Щоб зручно створювати та редагувати нотатки, використовуємо `ModelForm`. Вона автоматично згенерує потрібні поля на основі моделі.

Python

```
from django import forms
from .models import Note

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'text', 'reminder', 'category']
        widgets = {
            'reminder': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'text': forms.Textarea(attrs={'rows': 4}),
        }
```

## 3. Логіка та Extra-функціонал (`views.py`)

Тут ми реалізуємо:

1. Головну сторінку зі списком нотаток, **пошуком** та **фільтрацією** (Extra).
    
2. Створення нотатки.
    
3. Перегляд, **редагування** та **видалення** нотатки.
    

Python

```
from django.shortcuts import render, get_object_or_Hum404, redirect
from .models import Note, Category
from .forms import NoteForm

# Головна сторінка: Список, Пошук та Фільтрація
def note_list(request):
    notes = Note.objects.all().order_by('-created_at')
    categories = Category.objects.all()

    # Extra: Пошук за title
    search_query = request.GET.get('search', '')
    if search_query:
        notes = notes.filter(title__icontains=search_query)

    # Extra: Фільтрація за категорією
    category_id = request.GET.get('category', '')
    if category_id:
        notes = notes.filter(category_id=category_id)

    # Extra: Фільтрація за часом нагадування (наприклад, лише майбутні)
    filter_reminder = request.GET.get('reminder_filter', '')
    if filter_reminder == 'upcoming':
        from django.utils import timezone
        notes = notes.filter(reminder__gte=timezone.now())

    return render(request, 'notes/note_list.html', {
        'notes': notes,
        'categories': categories,
        'search_query': search_query,
    })

# 1. Створення нотатки
def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('note_list')
    else:
        form = NoteForm()
    return render(request, 'notes/note_form.html', {'form': form, 'action': 'Створити'})

# 2 & 3. Деталі, Редагування та Видалення
def note_detail_edit(request, pk):
    note = get_object_or_404(Note, pk=pk)
    
    if request.method == 'POST':
        # Якщо натиснули кнопку "Видалити"
        if 'delete' in request.POST:
            note.delete()
            return redirect('note_list')
        
        # Якщо це редагування (збереження форми)
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect('note_list')
    else:
        form = NoteForm(instance=note)
        
    return render(request, 'notes/note_detail.html', {'form': form, 'note': note})
```

## 4. Налаштування маршрутів (`urls.py`)

Зв'яжемо наші функції з URL-адресами:

Python

```
from django.urls import path
from . import views

urlpatterns = [
    path('', views.note_list, name='note_list'),
    path('new/', views.note_create, name='note_create'),
    path('<int:pk>/', views.note_detail_edit, name='note_detail_edit'),
]
```

## 5. Шаблони (HTML)

Для демонстрації логіки розіб'ємо інтерфейс на прості HTML-файли.

### Головна сторінка (`note_list.html`)

Тут виводяться форми пошуку, фільтрів та сам список нотаток.

HTML

```
<h2>Мої Нотатки</h2>
<a href="{% url 'note_create' %}">+ Створити нотатку</a>

<form method="GET" style="margin: 20px 0;">
    <input type="text" name="search" placeholder="Пошук за назвою..." value="{{ search_query }}">
    
    <select name="category">
        <option value="">Всі категорії</option>
        {% for cat in categories %}
            <option value="{{ cat.id }}">{{ cat.name }}</option>
        {% endfor %}
    </select>

    <select name="reminder_filter">
        <option value="">Всі нагадування</option>
        <option value="upcoming">Тільки майбутні</option>
    </select>

    <button type="submit">Застосувати</button>
</form>

<ul>
    {% for note in notes %}
        <li>
            <a href="{% url 'note_detail_edit' note.pk %}"><strong>{{ note.title }}</strong></a> 
            {% if note.category %}[{{ note.category.name }}]{% endif %}
            {% if note.reminder %}<small>⏰ {{ note.reminder }}</small>{% endif %}
        </li>
    {% empty %}
        <li>Нотаток не знайдено.</li>
    {% endfor %}
</ul>
```

### Вікно деталей, редагування та видалення (`note_detail.html`)

Суміщає відображення даних у формі, можливість апдейту та кнопку видалення.

HTML

```
<h2>Деталі нотатки: {{ note.title }}</h2>

<form method="POST">
    {% csrf_token %}
    {{ form.as_p }}
    
    <button type="submit" name="save">Зберегти зміни</button>
    <button type="submit" name="delete" onclick="return confirm('Ви впевнені, що хочете видалити цю нотатку?')" style="color: red;">
        Видалити нотатку
    </button>
</form>

<br>
<a href="{% url 'note_list' %}">Назад до списку</a>
```

### Форма створення (`note_form.html`)

Проста форма для додавання нового запису.

HTML

```
<h2>{{ action }} нотатку</h2>

<form method="POST">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Зберегти</button>
</form>

<br>
<a href="{% url 'note_list' %}">Скасувати</a>
```