## Крок 1: Підготовка та створення проєкту `notes_app`

Перед початком переконайся, що у твоєму віртуальному середовищі встановлено Django (`pip install django`).

1. **Створи Django-проєкт** з назвою `notes_app`. Для цього у терміналі виконай команду:
    
    Bash
    
    ```
    django-admin startproject notes_app
    ```
    
2. **Перейди в папку** щойно створеного проєкту:
    
    Bash
    
    ```
    cd notes_app
    ```
    

---

## Крок 2: Створення застосунку `notes`

У Django один проєкт може містити багато застосунків (apps). Давай створимо наш перший застосунок.

1. У терміналі (перебуваючи в папці з файлом `manage.py`) виконай:
    
    Bash
    
    ```
    python manage.py startapp notes
    ```
    
2. **Зареєструй застосунок** у проєкті. Відкрий файл `notes_app/settings.py`, знайди список `INSTALLED_APPS` і додай туди твій застосунок `'notes'`:
    
    Python
    
    ```
    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        # Твій новий застосунок:
        'notes',
    ]
    ```
    

---

## Крок 3: Написання View (Представлення)

Тепер створимо логіку, яка буде повертати фразу "Hello from Notes app.".

1. Відкрий файл `notes/views.py`.
    
2. Напиши простий view, який приймає запит (`request`) та повертає `HttpResponse`:
    
    Python
    
    ```
    from django.http import HttpResponse
    
    def notes_home(request):
        return HttpResponse("Hello from Notes app.")
    ```
    

---

## Крок 4: Налаштування URLs маршрутизації

Щоб Django розумів, за якою адресою показувати наш view, потрібно зв'язати їх через файли `urls.py`. Найбільш правильний підхід — це створити окремий `urls.py` всередині самого застосунку, а потім підключити його до головного.

1. **Створи новий файл** `urls.py` всередині папки `notes` (`notes/urls.py`) і додай туди такий код:
    
    Python
    
    ```
    from django.urls import path
    from . import views
    
    urlpatterns = [
        path('', views.notes_home, name='notes_home'),
    ]
    ```
    
2. **Підключи цей файл до головного `urls.py`** проєкту. Відкрий `notes_app/urls.py` та зміни його вміст, додавши функцію `include`:
    
    Python
    
    ```
    from django.contrib import admin
    from django.urls import path, include  # Не забудь імпортувати include
    
    urlpatterns = [
        path('admin/', admin.site.urls),
        # Підключаємо маршрути з нашого застосунку notes:
        path('notes/', include('notes.urls')), 
    ]
    ```
    
    _Примітка: ми вказали префікс `'notes/'`, тому наш текст буде доступний за адресою `/notes/`._
    

---

## Крок 5: Запуск та перевірка результату

Усе готово до старту! Повертайся в термінал.

1. **Запусти локальний сервер** розробки:
    
    Bash
    
    ```
    python manage.py runserver
    ```
    
2. Після запуску термінал покаже посилання (зазвичай це `http://127.0.0.1:8000/`).
    
3. Відкрий браузер і перейди за адресою: 👉 **`http://127.0.0.1:8000/notes/`**
    

На екрані ти побачиш чіткий і лаконічний напис:

> **Hello from Notes app.**