from django.test import TestCase

from .models import Category, Note


class NotesPageTests(TestCase):
    def test_notes_page_displays_note_from_database(self):
        category = Category.objects.create(title="Study")
        Note.objects.create(title="Python", text="Repeat Django models", category=category)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python")
        self.assertContains(response, "Study")
