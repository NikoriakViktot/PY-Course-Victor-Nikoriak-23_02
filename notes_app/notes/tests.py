from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Category, Note
from .forms import NoteForm
class NoteUnitTestCase(TestCase):
    """
    Unit-тести для перевірки збереження, зміни та валідації даних нотаток.
    """
    def setUp(self):
        # Створюємо базову категорію для тестів
        self.category = Category.objects.create(title="робота")
    def test_note_creation(self):
        """Перевірка успішного створення та збереження нотатки в базу даних."""
        reminder_time = timezone.now() + timedelta(days=1)
        note = Note.objects.create(
            title="тестова нотатка",
            text="текст для тесту",
            reminder=reminder_time,
            category=self.category
        )
        # Перевіряємо, чи правильно збереглися дані
        self.assertEqual(note.title, "тестова нотатка")
        self.assertEqual(note.text, "текст для тесту")
        self.assertEqual(note.reminder, reminder_time)
        self.assertEqual(note.category, self.category)
        # Перевіряємо роботу методу __str__
        self.assertEqual(str(note), "тестова нотатка")
    def test_note_update(self):
        """Перевірка модифікації та зміни існуючої нотатки."""
        note = Note.objects.create(
            title="стара назва",
            text="старий текст",
            category=self.category
        )
        # Змінюємо поля нотатки
        note.title = "нова назва"
        note.text = "новий текст"
        note.save()
        # Оновлюємо об'єкт з бази даних
        note.refresh_from_db()
        self.assertEqual(note.title, "нова назва")
        self.assertEqual(note.text, "новий текст")
    def test_note_form_validation(self):
        """Перевірка валідації форми NoteForm з коректними даними."""
        form_data = {
            'title': 'назва з форми',
            'text': 'текст з форми',
            'category': self.category.id,
            'reminder': ''  # Поле необов'язкове (blank=True)
        }
        form = NoteForm(data=form_data)
        self.assertTrue(form.is_valid())
class NoteIntegrationTestCase(TestCase):
    """
    Extra: Інтеграційні тести для перевірки HTTP API та логіки View за допомогою тестового клієнта.
    """
    def setUp(self):
        # Ініціалізуємо тестовий клієнт
        self.client = Client()
        self.category = Category.objects.create(title="особисте")
        # Створюємо початкову нотатку для тестів редагування/видалення/пошуку
        self.note = Note.objects.create(
            title="важлива зустріч",
            text="не забути про здзвони",
            category=self.category
        )
    def test_main_page_get_and_filtering(self):
        """Тест отримання головної сторінки, пошуку та фільтрації."""
        url = reverse('main_page')
        # Перевірка звичайного GET-запиту
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "важлива зустріч")
        # Перевірка пошуку за title (Extra функціонал)
        response_search = self.client.get(url, {'search': 'важлива'})
        self.assertContains(response_search, "важлива зустріч")
        # Перевірка пошуку, який не має повернути результатів
        response_empty = self.client.get(url, {'search': 'відпустка'})
        self.assertNotContains(response_empty, "важлива зустріч")
    def test_note_creation_via_post(self):
        """Тест створення нотатки через POST-запит на головну сторінку."""
        url = reverse('main_page')
        post_data = {
            'title': 'нова нотатка через api',
            'text': 'створено в інтеграційному тесті',
            'category': self.category.id,
            'reminder': ''
        }
        # Відправляємо POST-запит (імітація натискання "Зберегти нотатку")
        response = self.client.post(url, data=post_data)
        # Перевіряємо редірект після успішного створення
        self.assertEqual(response.status_code, 302)
        # Перевіряємо, чи з'явився новий запис у базі даних
        self.assertTrue(Note.objects.filter(title='нова нотатка через api').exists())
    def test_note_detail_and_update_via_post(self):
        """Тест перегляду деталей та редагування через POST на сторінку деталей."""
        url = reverse('note_detail', kwargs={'note_id': self.note.id})
        # Перевірка відображення вікна деталей
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        # Дані для модифікації нотатки
        updated_data = {
            'title': 'оновлена зустріч',
            'text': 'текст було змінено через клієнт',
            'category': self.category.id,
            'reminder': ''
        }
        # Відправляємо POST для оновлення полів
        response_post = self.client.post(url, data=updated_data)
        self.assertEqual(response_post.status_code, 302)  # Очікуємо редірект на цю ж сторінку деталей
        # Перевіряємо зміни в базі даних
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, 'оновлена зустріч')
    def test_note_deletion_via_post(self):
        """Тест видалення нотатки через передачу параметра 'delete' у POST-запиті."""
        url = reverse('note_detail', kwargs={'note_id': self.note.id})
        # Надсилаємо POST-запит із прапорцем delete (імітуємо натискання кнопки видалення)
        response = self.client.post(url, data={'delete': ''})
        # Має відбутися редірект на головну сторінку ('main_page')
        self.assertEqual(response.status_code, 302)
        # Перевіряємо, що нотатки більше немає в базі даних
        self.assertFalse(Note.objects.filter(id=self.note.id).exists())

