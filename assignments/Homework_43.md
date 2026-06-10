Для оновлення візуального стилю чудово підійде **Bootstrap 5**. 
Оскільки у Django шаблони можуть успадковувати загальну структуру, найкраще створити базовий шаблон `base.html` з навігаційною панеллю, а інші сторінки (список нотаток та форму) "вбудовувати" в нього.

## 1. Головний шаблон з навігаційною панеллю (`base.html`)


HTML

```
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Нотатки{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
</head>
<body class="bg-light">

    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4 shadow-sm">
        <div class="container">
            <a class="navbar-brand d-flex align-items-center" href="{% url 'note_list' %}">
                <i class="bi bi-journal-text me-2 fs-3 text-warning"></i>
                <span class="fw-bold tracking-wide">DjangoNotes</span>
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link {% if request.resolver_match.url_name == 'note_list' %}active{% endif %}" href="{% url 'note_list' %}">
                            <i class="bi bi-house-door me-1"></i> Головна
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="btn btn-warning ms-lg-2 mt-2 mt-lg-0 d-flex align-items-center" href="{% url 'note_create' %}">
                            <i class="bi bi-plus-circle me-1"></i> Створити нотатку
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container">
        {% block content %}
        {% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

## 2. Оновлена головна сторінка (`note_list.html`)

Переписуємо головну сторінку. Ми перетворимо список на гарні **картки (Cards)**, акуратно оформимо форму пошуку та фільтрації, а також додамо колірні акценти для категорій та нагадувань.

HTML

```
{% extends 'base.html' %}

{% block title %}Мої Нотатки{% endblock %}

{% block content %}
<div class="row mb-4 align-items-center">
    <div class="col">
        <h2 class="fw-bold text-secondary mb-0">Мої Нотатки</h2>
    </div>
</div>

<div class="card shadow-sm border-0 mb-4">
    <div class="card-body">
        <form method="GET" class="row g-3">
            <div class="col-md-4">
                <div class="input-group">
                    <span class="input-group-text bg-white text-muted"><i class="bi bi-search"></i></span>
                    <input type="text" name="search" class="form-control" placeholder="Пошук за назвою..." value="{{ search_query }}">
                </div>
            </div>
            
            <div class="col-md-3">
                <select name="category" class="form-select">
                    <option value="">Всі категорії</option>
                    {% for cat in categories %}
                        <option value="{{ cat.id }}" {% if request.GET.category == cat.id|slugify %}selected{% endif %}>{{ cat.name }}</option>
                    {% endfor %}
                </select>
            </div>

            <div class="col-md-3">
                <select name="reminder_filter" class="form-select">
                    <option value="">Всі нагадування</option>
                    <option value="upcoming" {% if request.GET.reminder_filter == 'upcoming' %}selected{% endif %}>Тільки майбутні</option>
                </select>
            </div>

            <div class="col-md-2 d-grid">
                <button type="submit" class="btn btn-primary">Застосувати</button>
            </div>
        </form>
    </div>
</div>

<div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
    {% for note in notes %}
        <div class="col">
            <div class="card h-100 shadow-sm border-0 position-relative hover-shadow">
                <div class="card-body d-flex flex-column">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h5 class="card-title fw-bold text-dark mb-0">{{ note.title }}</h5>
                        {% if note.category %}
                            <span class="badge bg-info text-dark">{{ note.category.name }}</span>
                        {% endif %}
                    </div>
                    
                    <p class="card-text text-muted flex-grow-1">
                        {{ note.text|truncatewords:20 }}
                    </p>
                    
                    <hr class="text-black-50 my-2">
                    
                    <div class="d-flex justify-content-between align-items-center mt-auto">
                        {% if note.reminder %}
                            <small class="text-danger fw-semibold">
                                <i class="bi bi-bell-fill me-1"></i> {{ note.reminder|date:"d.m.Y H:i" }}
                            </small>
                        {% else %}
                            <small class="text-muted"><i class="bi bi-bell-slash me-1"></i> Немає</small>
                        {% endif %}
                        
                        <a href="{% url 'note_detail_edit' note.pk %}" class="btn btn-sm btn-outline-secondary">
                            <i class="bi bi-pencil-square"></i> Деталі
                        </a>
                    </div>
                </div>
            </div>
        </div>
    {% empty %}
        <div class="col-12 text-center my-5">
            <div class="text-muted fs-4">
                <i class="bi bi-sticky fs-1 d-block mb-3 text-black-50"></i>
                Нотаток не знайдено.
            </div>
        </div>
    {% endfor %}
</div>
{% endblock %}
```

## 3. Оновлена форма створення та редагування (`note_form.html` та `note_detail.html`)

За замовчуванням Django рендерить форми через `{{ form.as_p }}` як звичайні інпути без стилів. Щоб автоматично додати до всіх полей форми класи Bootstrap (`form-control`, `form-select`), ми можемо скористатися вбудованим у Django інструментом циклу або оновити віджети безпосередньо у `forms.py`.

Ось найчистіший спосіб зробити це без встановлення додаткових бібліотек — оновимо `forms.py`:

Python

```
# forms.py
from django import forms
from .models import Note

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'text', 'reminder', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введіть назву нотатки'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Ваш текст тут...'}),
            'reminder': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
```

Тепер наші HTML-файли форм виглядатимуть дуже професійно.

### Шаблон створення (`note_form.html`)

HTML

```
{% extends 'base.html' %}

{% block title %}{{ action }} нотатку{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8 col-lg-6">
        <div class="card shadow border-0">
            <div class="card-body p-4">
                <h3 class="card-title fw-bold text-center mb-4 text-primary">
                    <i class="bi bi-file-earmark-plus me-2"></i>{{ action }} нотатку
                </h3>
                
                <form method="POST" novalidate>
                    {% csrf_token %}
                    
                    {% for field in form %}
                        <div class="mb-3">
                            <label class="form-label fw-semibold text-secondary">{{ field.label }}</label>
                            {{ field }}
                            {% if field.errors %}
                                <div class="text-danger small mt-1">
                                    {{ field.errors|striptags }}
                                </div>
                            {% endif %}
                        </div>
                    {% endfor %}
                    
                    <div class="d-grid gap-2 d-md-flex justify-content-md-end mt-4">
                        <a href="{% url 'note_list' %}" class="btn btn-light me-md-2">Скасувати</a>
                        <button type="submit" class="btn btn-success px-4">Зберегти нотатку</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Шаблон деталей, редагування та видалення (`note_detail.html`)

HTML

```
{% extends 'base.html' %}

{% block title %}Нотатка: {{ note.title }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8 col-lg-6">
        <div class="card shadow border-0">
            <div class="card-body p-4">
                <h3 class="card-title fw-bold text-center mb-4 text-dark">
                    <i class="bi bi-pencil-square me-2 text-warning"></i>Деталі та Редагування
                </h3>
                
                <form method="POST">
                    {% csrf_token %}
                    
                    {% for field in form %}
                        <div class="mb-3">
                            <label class="form-label fw-semibold text-secondary">{{ field.label }}</label>
                            {{ field }}
                            {% if field.errors %}
                                <div class="text-danger small mt-1">
                                    {{ field.errors|striptags }}
                                </div>
                            {% endif %}
                        </div>
                    {% endfor %}
                    
                    <hr class="my-4">
                    
                    <div class="d-flex flex-column flex-sm-row justify-content-between gap-2">
                        <button type="submit" name="delete" class="btn btn-outline-danger" onclick="return confirm('Ви впевнені, що хочете остаточно видалити цю нотатку?')">
                            <i class="bi bi-trash3 me-1"></i> Видалити
                        </button>
                        
                        <div class="d-flex gap-2 justify-content-end">
                            <a href="{% url 'note_list' %}" class="btn btn-light">Назад</a>
                            <button type="submit" name="save" class="btn btn-primary px-4">
                                <i class="bi bi-check-circle me-1"></i> Зберегти
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```