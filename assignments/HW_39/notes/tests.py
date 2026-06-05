from django.test import TestCase
from django.urls import reverse
from .models import Note, Category


class NoteCRUDTests(TestCase):

    def setUp(self):
        """
        Цей метод виконується перед КОЖНИМ тестом.
        Створюємо тестову категорію, щоб прив'язувати її до нотаток.
        """
        self.category = Category.objects.create(title="Навчання")

    def test_notes_index_view(self):
        """Тестуємо, що головна сторінка відкривається успішно (код 200)"""
        response = self.client.get(reverse('notes_index'))
        self.assertEqual(response.status_code, 200)
        # Перевіряємо, чи використовується правильний HTML-шаблон
        self.assertTemplateUsed(response, 'notes/index.html')

    def test_note_creation_via_post(self):
        """Тестуємо СТВОРЕННЯ нотатки через POST-запит форми"""
        # Емулюємо заповнення форми створення на сайті
        data = {
            'title': 'Нова тестова нотатка',
            'text': 'Текст для перевірки юніт-тесту',
            'category': self.category.id,
            'reminder': ''
        }
        response = self.client.post(reverse('note_create'), data=data)

        # Після успішного створення має бути редірект на головну (код 302)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('notes_index'))

        # Перевіряємо, чи дійсно запис з'явився в базі даних
        self.assertTrue(Note.objects.filter(title='Нова тестова нотатка').exists())

    def test_note_editing_via_post(self):
        """Тестуємо РЕДАГУВАННЯ (зміну) деталей наявної нотатки"""
        # Спочатку створюємо нотатку, яку будемо міняти
        note = Note.objects.create(
            title="Старий заголовок",
            text="Старий текст",
            category=self.category
        )

        # Емулюємо відправку оновлених даних у вікні редагування
        updated_data = {
            'title': 'Оновлений заголовок',
            'text': 'Оновлений текст нотатки',
            'category': self.category.id,
            'reminder': ''
        }
        response = self.client.post(reverse('note_detail', args=[note.id]), data=updated_data)

        # Після оновлення теж має бути редірект
        self.assertEqual(response.status_code, 302)

        # Оновлюємо дані об'єкта з бази даних
        note.refresh_from_db()
        # Перевіряємо, чи змінилися поля
        self.assertEqual(note.title, 'Оновлений заголовок')
        self.assertEqual(note.text, 'Оновлений текст нотатки')

    def test_note_deletion_via_post(self):
        """Тестуємо ВІЗУАЛЬНЕ ВИДАЛЕННЯ нотатки з бази даних"""
        # Створюємо нотатку для видалення
        note = Note.objects.create(
            title="Нотатка для видалення",
            text="Цей текст буде видалено",
            category=self.category
        )

        # Відправляємо POST-запит на маршрут видалення
        response = self.client.post(reverse('note_delete', args=[note.id]))

        # Має відбутися редірект на головну
        self.assertEqual(response.status_code, 302)

        # Перевіряємо, що нотатки з таким ID більше немає в базі даних
        self.assertFalse(Note.objects.filter(id=note.id).exists())