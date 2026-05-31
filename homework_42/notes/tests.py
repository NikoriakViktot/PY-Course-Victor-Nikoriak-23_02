import json

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Note


class NotesModelTests(TestCase):
    def test_category_and_note_string_representations(self):
        category = Category.objects.create(title="Навчання")
        note = Note.objects.create(
            title="Повторити Django",
            text="Форми, моделі та маршрути",
            category=category,
        )

        self.assertEqual(str(category), "Навчання")
        self.assertEqual(str(note), "Повторити Django")
        self.assertEqual(
            note.get_absolute_url(), reverse("note_detail", kwargs={"note_id": note.id})
        )


class NotePersistenceUnitTests(TestCase):
    def setUp(self):
        self.personal = Category.objects.create(title="Особисте")
        self.work = Category.objects.create(title="Робота")

    def test_save_note_persists_fields_and_timestamps(self):
        reminder = timezone.now() + timezone.timedelta(hours=2)

        note = Note.objects.create(
            title="Купити продукти",
            text="Молоко, хліб, сир",
            category=self.personal,
            reminder=reminder,
        )

        saved_note = Note.objects.get(id=note.id)
        self.assertEqual(saved_note.title, "Купити продукти")
        self.assertEqual(saved_note.text, "Молоко, хліб, сир")
        self.assertEqual(saved_note.category, self.personal)
        self.assertEqual(saved_note.reminder, reminder)
        self.assertIsNotNone(saved_note.created_at)
        self.assertIsNotNone(saved_note.updated_at)

    def test_change_note_persists_updated_fields(self):
        note = Note.objects.create(
            title="Стара назва",
            text="Старий текст",
            category=self.personal,
        )
        created_at = note.created_at
        new_reminder = timezone.now() + timezone.timedelta(days=3)

        note.title = "Нова назва"
        note.text = "Новий текст"
        note.category = self.work
        note.reminder = new_reminder
        note.save()

        changed_note = Note.objects.get(id=note.id)
        self.assertEqual(changed_note.title, "Нова назва")
        self.assertEqual(changed_note.text, "Новий текст")
        self.assertEqual(changed_note.category, self.work)
        self.assertEqual(changed_note.reminder, new_reminder)
        self.assertEqual(changed_note.created_at, created_at)
        self.assertGreaterEqual(changed_note.updated_at, created_at)


class NotesViewTests(TestCase):
    def setUp(self):
        self.study = Category.objects.create(title="Навчання")
        self.work = Category.objects.create(title="Робота")
        self.note = Note.objects.create(
            title="Django форми",
            text="Потрібно повторити ModelForm",
            category=self.study,
            reminder=timezone.now() + timezone.timedelta(days=1),
        )
        Note.objects.create(
            title="Зустріч",
            text="Обговорити задачі команди",
            category=self.work,
        )

    def test_notes_list_renders_notes(self):
        response = self.client.get(reverse("notes_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django форми")
        self.assertContains(response, "Зустріч")

    def test_notes_list_filters_by_text_query(self):
        response = self.client.get(reverse("notes_list"), {"query": "ModelForm"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django форми")
        self.assertNotContains(response, "Зустріч")

    def test_notes_list_filters_by_category(self):
        response = self.client.get(reverse("notes_list"), {"category": self.work.id})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Зустріч")
        self.assertNotContains(response, "Django форми")

    def test_note_create(self):
        response = self.client.post(
            reverse("note_create"),
            {
                "title": "Нова нотатка",
                "text": "Текст нової нотатки",
                "category": self.study.id,
                "reminder": "",
            },
        )

        note = Note.objects.get(title="Нова нотатка")
        self.assertRedirects(response, note.get_absolute_url())

    def test_note_update(self):
        response = self.client.post(
            reverse("note_detail", kwargs={"note_id": self.note.id}),
            {
                "title": "Оновлена назва",
                "text": self.note.text,
                "category": self.note.category.id,
                "reminder": "",
            },
        )

        self.assertRedirects(response, self.note.get_absolute_url())
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, "Оновлена назва")

    def test_note_delete_requires_post(self):
        get_response = self.client.get(
            reverse("note_delete", kwargs={"note_id": self.note.id})
        )
        self.assertRedirects(get_response, self.note.get_absolute_url())
        self.assertTrue(Note.objects.filter(id=self.note.id).exists())

        post_response = self.client.post(
            reverse("note_delete", kwargs={"note_id": self.note.id})
        )
        self.assertRedirects(post_response, reverse("notes_list"))
        self.assertFalse(Note.objects.filter(id=self.note.id).exists())


class CategoryViewTests(TestCase):
    def test_category_crud(self):
        create_response = self.client.post(
            reverse("category_create"), {"title": "Особисте"}
        )
        self.assertRedirects(create_response, reverse("categories_list"))

        category = Category.objects.get(title="Особисте")
        update_response = self.client.post(
            reverse("category_update", kwargs={"category_id": category.id}),
            {"title": "Приватне"},
        )
        self.assertRedirects(update_response, reverse("categories_list"))
        category.refresh_from_db()
        self.assertEqual(category.title, "Приватне")

        delete_response = self.client.post(
            reverse("category_delete", kwargs={"category_id": category.id})
        )
        self.assertRedirects(delete_response, reverse("categories_list"))
        self.assertFalse(Category.objects.filter(id=category.id).exists())


class NoteApiIntegrationTests(TestCase):
    def setUp(self):
        self.study = Category.objects.create(title="Навчання")
        self.work = Category.objects.create(title="Робота")
        self.note = Note.objects.create(
            title="Початкова нотатка",
            text="Початковий текст",
            category=self.study,
        )

    def test_api_lists_notes_with_test_client(self):
        response = self.client.get(reverse("api_notes"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["notes"]), 1)
        self.assertEqual(data["notes"][0]["title"], "Початкова нотатка")
        self.assertEqual(data["notes"][0]["category"], self.study.id)

    def test_api_creates_note_with_test_client(self):
        payload = {
            "title": "API нотатка",
            "text": "Створено через JSON API",
            "category": self.work.id,
            "reminder": "2026-06-01T09:30",
        }

        response = self.client.post(
            reverse("api_notes"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        note = Note.objects.get(title="API нотатка")
        data = response.json()
        self.assertEqual(data["note"]["id"], note.id)
        self.assertEqual(data["note"]["text"], "Створено через JSON API")
        self.assertEqual(note.category, self.work)

    def test_api_updates_note_with_test_client(self):
        payload = {
            "title": "Оновлено через API",
            "text": "Новий текст через тестовий клієнт",
            "category": self.work.id,
        }

        response = self.client.patch(
            reverse("api_note_detail", kwargs={"note_id": self.note.id}),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.note.refresh_from_db()
        data = response.json()
        self.assertEqual(self.note.title, "Оновлено через API")
        self.assertEqual(self.note.text, "Новий текст через тестовий клієнт")
        self.assertEqual(self.note.category, self.work)
        self.assertEqual(data["note"]["title"], "Оновлено через API")

    def test_api_returns_validation_errors_for_invalid_create_payload(self):
        response = self.client.post(
            reverse("api_notes"),
            data=json.dumps({"title": "Без категорії"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())
        self.assertFalse(Note.objects.filter(title="Без категорії").exists())