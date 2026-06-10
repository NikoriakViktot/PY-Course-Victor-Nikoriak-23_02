Для Django найкраще використовувати вбудований модуль `django.test.TestCase`. Він автоматично створює чисту (тестову) базу даних перед початком тестів і очищає її після завершення, тому реальні дані ніяк не постраждають.

## Код тестів (`tests.py`)

Додайте цей код у файл `tests.py` вашого додатка:

Python

```
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Note, Category

class NoteCRUDAndExtraTests(TestCase):

    def setUp(self):
        """
        Початкове налаштування: створюємо категорію та одну нотатку
        для подальших тестів редагування, видалення та фільтрації.
        """
        self.category_work = Category.objects.create(name="Робота")
        self.category_home = Category.objects.create(name="Дім")
        
        self.note = Note.objects.create(
            title="Купити молоко",
            text="Потрібно купити 2л молока",
            category=self.category_home,
            reminder=timezone.now() + timezone.timedelta(days=1)  # Майбутнє нагадування
        )

    # ==========================================
    # 1. ТЕСТИ ДЛЯ CRUD (Створення, Редагування, Видалення)
    # ==========================================

    def test_note_creation(self):
        """Тест створення нотатки через POST-запит."""
        url = reverse('note_create')
        data = {
            'title': 'Нова нотатка',
            'text': 'Зміст нової нотатки',
            'category': self.category_work.id,
            'reminder': (timezone.now() + timezone.timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')
        }
        
        response = self.client.post(url, data)
        
        # Перевіряємо редирект на головну сторінку після успішного створення
        self.assertEqual(response.status_code, 302)
        # Перевіряємо, чи з'явилася нотатка в базі даних
        self.assertTrue(Note.objects.filter(title='Нова нотатка').exists())

    def test_note_edit(self):
        """Тест зміни (редагування) деталей нотатки."""
        url = reverse('note_detail_edit', kwargs={'pk': self.note.pk})
        data = {
            'title': 'Купити молоко та хліб',  # Змінена назва
            'text': self.note.text,
            'category': self.note.category.id,
            'save': ''  # Імітуємо натискання кнопки збереження (name="save")
        }
        
        response = self.client.post(url, data)
        
        # Перевіряємо редирект
        self.assertEqual(response.status_code, 302)
        # Оновлюємо об'єкт з бази даних
        self.note.refresh_from_db()
        # Перевіряємо, чи назва дійсно змінилася
        self.assertEqual(self.note.title, 'Купити молоко та хліб')

    def test_note_delete(self):
        """Тест видалення нотатки."""
        url = reverse('note_detail_edit', kwargs={'pk': self.note.pk})
        # Надсилаємо параметр 'delete', який обробляється у views.py
        data = {'delete': ''}
        
        response = self.client.post(url, data)
        
        # Перевіряємо редирект
        self.assertEqual(response.status_code, 302)
        # Перевіряємо, чи нотатка зникла з бази даних
        self.assertFalse(Note.objects.filter(pk=self.note.pk).exists())


    # ==========================================
    # 2. ТЕСТИ ДЛЯ EXTRA-ФУНКЦІОНАЛУ (Пошук, Фільтрація)
    # ==========================================

    def test_search_by_title(self):
        """Тест пошуку нотатки за title."""
        # Створюємо ще одну нотатку, яка не має підходити під пошук
        Note.objects.create(title="Здати звіт", text="Важливо", category=self.category_work)
        
        url = reverse('note_list')
        # Робимо GET-запит із параметром пошуку 'search'
        response = self.client.get(url, {'search': 'молоко'})
        
        self.assertEqual(response.status_code, 200)
        # Перевіряємо, що в результатах є нотатка "Купити молоко"
        self.assertContains(response, "Купити молоко")
        # Перевіряємо, що нотатки "Здати звіт" немає в результатах пошуку
        self.assertNotContains(response, "Здати звіт")

    def test_filter_by_category(self):
        """Тест фільтрації нотаток за категорією."""
        # Створюємо нотатку в категорії "Робота"
        work_note = Note.objects.create(title="Робоча задача", text="Текст", category=self.category_work)
        
        url = reverse('note_list')
        # Фільтруємо за категорією "Дім"
        response = self.client.get(url, {'category': self.category_home.id})
        
        self.assertContains(response, "Купити молоко")
        self.assertNotContains(response, "Робоча задача")

    def test_filter_by_reminder(self):
        """Тест фільтрації за часом нагадування (майбутні нагадування)."""
        # Створюємо нотатку з протермінованим нагадуванням (в минулому)
        past_note = Note.objects.create(
            title="Минула подія", 
            text="Текст", 
            reminder=timezone.now() - timezone.timedelta(days=2)
        )
        
        url = reverse('note_list')
        # Застосовуємо фільтр 'upcoming'
        response = self.client.get(url, {'reminder_filter': 'upcoming'})
        
        # Перевіряємо, що майбутня нотатка відображається, а минула — ні
        self.assertContains(response, "Купити молоко")
        self.assertNotContains(response, "Минула подія")
```

## Як запустити ці тести?

У терміналі (в кореневій директорії проєкту, де знаходиться файл `manage.py`) виконайте команду:

Bash

```
python manage.py test
```