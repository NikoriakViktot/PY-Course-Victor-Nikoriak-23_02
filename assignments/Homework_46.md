## Крок 1. Налаштування в Telegram (Бот та Канал)

1. **Створення бота:**
    
    - Знайдіть у Telegram бота **@BotFather**.
        
    - Надішліть йому команду `/newbot`.
        
    - Вкажіть назву бота та його унікальний юзернейм (наприклад, `MyNotesDjangoBot`).
        
    - **Скопіюйте отриманий токен** (він виглядає як `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).
        
2. **Створення каналу:**
    
    - Створіть новий **Публічний** або **Приватний** канал у Telegram.
        
    - Додайте вашого створеного бота до цього каналу **як адміністратора** з правом публікації повідомлень.
        
    - **Дізнайтеся ID каналу:**
        
        - Якщо канал _публічний_, його ID — це його юзернейм (наприклад, `@my_notes_channel`).
            
        - Якщо канал _приватний_, найпростіший спосіб дізнатися ID: перешліть будь-який пост із каналу спеціальному боту `@userinfobot` або `@JsonDumpBot`, і він поверне ID, який зазвичай починається з `-100` (наприклад, `-1001234567890`).
            

## Крок 2. Налаштування конфігурації в Django

Щоб не "хардкодити" токен у коді (це небезпечно), додамо конфігурацію у файл `settings.py`.

Python

```
# settings.py (додайте в кінець файлу)

TELEGRAM_BOT_TOKEN = 'ВАШ_ТОКЕН_ВІД_BOTFATHER'
TELEGRAM_CHANNEL_ID = 'ВАШ_ID_КАНАЛУ'  # Наприклад, '@my_notes_channel' або -1001234567890
```

## Крок 3. Створення сервісу надсилання повідомлень

Створимо окрему функцію для відправки повідомлень через Telegram API. Для цього нам знадобиться бібліотека `requests`, яка зазвичай уже є в оточенні (якщо ні, виконайте `pip install requests`).

Створіть файл `utils.py` у папці вашого Django-додатка:

Python

```
# utils.py
import requests
from django.conf import settings

def send_telegram_notification(note):
    """
    Функція для надсилання форматованого тексту нотатки в Telegram канал.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    channel_id = settings.TELEGRAM_CHANNEL_ID
    
    # Формуємо красивий текст повідомлення за допомогою HTML-розмітки
    text = (
        f"📌 <b>НОВА НОТАТКА СТВОРЕНА</b>\n\n"
        f"📝 <b>Назва:</b> {note.title}\n"
    )
    
    if note.category:
        text += f"📂 <b>Категорія:</b> {note.category.name}\n"
        
    if note.reminder:
        # Форматуємо дату для зручного читання
        formatted_date = note.reminder.strftime('%d.%m.%Y %H:%M')
        text += f"⏰ <b>Нагадування:</b> {formatted_date}\n"
        
    text += f"\n📖 <b>Текст:</b>\n{note.text}"

    # URL для запиту до API Telegram
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        'chat_id': channel_id,
        'text': text,
        'parse_mode': 'HTML'  # Дозволяє використовувати теги <b>, <i> тощо.
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        # Якщо Telegram повернув помилку (наприклад, бота немає в адмінах), ми побачимо це в консолі
        if response.status_code != 200:
            print(f"Помилка Telegram API: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Не вдалося з'єднатися з Telegram: {e}")
```

## Крок 4. Інтеграція у представлення (`views.py`)

Тепер викликатимемо цю функцію щоразу, коли користувач успішно створює нотатку через форму. Оновимо функцію `note_create`:

Python

```
# views.py
from django.shortcuts import render, redirect
from .forms import NoteForm
from .utils import send_telegram_notification  # Імпортуємо наш сервіс

def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            # Зберігаємо нотатку в базу даних
            note = form.save()
            
            # Викликаємо функцію відправки в Telegram
            send_telegram_notification(note)
            
            return redirect('note_list')
    else:
        form = NoteForm()
    return render(request, 'notes/note_form.html', {'form': form, 'action': 'Створити'})
```