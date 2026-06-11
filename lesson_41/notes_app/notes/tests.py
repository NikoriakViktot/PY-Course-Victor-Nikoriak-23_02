from django.test import TestCase
from django.urls import reverse

from .models import Category, Note


class NotesPageTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Study")
        self.note = Note.objects.create(title="Python", text="Repeat Django forms", category=self.category)

    def test_notes_page_displays_note_from_database(self):
        response = self.client.get(reverse("notes_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python")
        self.assertContains(response, "Study")

    def test_create_note(self):
        response = self.client.post(
            reverse("note_create"),
            {
                "title": "New note",
                "text": "Create note with form",
                "reminder": "",
                "category": self.category.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Note.objects.filter(title="New note").exists())

    def test_update_note(self):
        response = self.client.post(
            reverse("note_detail", args=[self.note.pk]),
            {
                "title": "Updated note",
                "text": "Updated text",
                "reminder": "",
                "category": self.category.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, "Updated note")

    def test_delete_note(self):
        response = self.client.post(reverse("note_delete", args=[self.note.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Note.objects.filter(pk=self.note.pk).exists())
