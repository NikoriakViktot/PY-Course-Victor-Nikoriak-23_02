
### Крок 1: Створення моделей та зв'язку (`models.py`)

У файлі `models.py` створюємо дві моделі. Зв'язок «один до багатьох» (у однієї категорії може бути багато нотаток) реалізується через `ForeignKey`.

Python

```
from django.db import models

class Category(models.Model):
    title = models.CharField(max_length=100, verbose_name="Назва категорії")

    def __str__(self):
        return self.title

class Note(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст нотатки")
    reminder = models.DateTimeField(null=True, blank=True, verbose_name="Нагадування")
    
    # Зовнішній ключ (Foreign Key) для зв'язку з категорією
    # models.SET_NULL дозволить зберегти нотатку, якщо категорію буде видалено
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="notes",
        verbose_name="Категорія"
    )

    def __str__(self):
        return self.title
```

### Крок 2: Налаштування PostgreSQL (Extra завдання)

За замовчуванням Django використовує SQLite. Щоб замінити її на PostgreSQL:

1. **Встановіть драйвер** для роботи Python з PostgreSQL у вашому віртуальному середовищі:
    
    Bash
    
    ```
    pip install psycopg2-binary
    ```
    
2. **Оновіть налаштування** у файлі `settings.py` вашого проєкту в секції `DATABASES`. Замініть стандартний блок на такий (вказавши ваші дані користувача PostgreSQL):
    

Python

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'notes_db',          # Назва бази даних, яку ви створили в Postgres
        'USER': 'your_postgres_user', # Ваш користувач (наприклад, postgres)
        'PASSWORD': 'your_password',  # Ваш пароль
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

_Перед наступним кроком переконайтеся, що база даних `notes_db` вже створена у вашій СУБД PostgreSQL._

### Крок 3: Створення та застосування міграцій

Тепер, коли Django знає про нові моделі та підключений до PostgreSQL, генеруємо файли міграцій та застосовуємо їх до бази даних. Виконайте в терміналі:

Bash

```
python manage.py makemigrations
python manage.py migrate
```

Після цього в PostgreSQL автоматично створяться відповідні таблиці.

### Крок 4: Наповнення тестовими даними

Наповнити базу даних можна кількома способами: через адмін-панель Django, за допомогою фікстур (JSON) або через командний рядок (`shell`).

Найшвидший спосіб через `python manage.py shell`:

Python

```
from your_app.models import Category, Note
from django.utils import timezone

# Створюємо категорії
cat1 = Category.objects.create(title="Робота")
cat2 = Category.objects.create(title="Особисте")

# Створюємо нотатки із прив'язкою до категорій та нагадувань
Note.objects.create(
    title="Купити продукти", 
    text="Молоко, хліб, кава, куряче філе та овочі на вечерю.", 
    category=cat2
)

Note.objects.create(
    title="Проєкт на Arch Linux", 
    text="Налаштувати резервне копіювання конфігів та оновити пакети в системі.", 
    category=cat1,
    reminder=timezone.now() + timezone.timedelta(days=1)
)

Note.objects.create(
    title="Тренування", 
    text="Комплекс вправ із гумовими петлями (YTW та розведення на грудні м'язи).", 
    category=cat2
)
```

### Крок 5: Виведення даних через View (`views.py`)

Замість статичного масиву (тестових даних) з попереднього уроку, тепер ми робимо запит до бази даних PostgreSQL за допомогою Django ORM.

Python

```
from django.shortcuts import render
from .models import Note

def index(request):
    # Отримуємо всі нотатки з бази даних. 
    # select_related('category') оптимізує запит, щоб одразу завантажити пов'язані категорії
    notes = Note.objects.select_related('category').all()
    
    # Передаємо контекст у шаблон, створений на попередньому уроці
    return render(request, 'index.html', {'notes': notes})
```

### Крок 6: Оновлення HTML-шаблону (`templates/index.html`)

Тепер переписуємо статичний блок карток на динамічний цикл за допомогою шаблонізатора Django, додаючи вивід категорії та нагадування:

HTML

```
<div class="notes-grid">
    
    {% for note in notes %}
    <div class="note-card">
        {% if note.category %}
            <span class="category-badge">{{ note.category.title }}</span>
        {% endif %}
        
        <h3 class="note-title">{{ note.title }}</h3>
        <p class="note-text">{{ note.text }}</p>
        
        <div class="note-footer">
            {% if note.reminder %}
                <span class="reminder-zone">⏰ {{ note.reminder|date:"d.m.Y H:i" }}</span>
            {% endif %}
        </div>
    </div>
    {% empty %}
        <p>Нотаток поки немає.</p>
    {% endfor %}

</div>
```