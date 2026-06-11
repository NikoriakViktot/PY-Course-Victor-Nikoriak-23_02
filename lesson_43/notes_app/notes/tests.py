import json

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import NoteForm
from .models import Category, Note


class NoteUnitTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Study")
        self.other_category = Category.objects.create(title="Work")
        self.note = Note.objects.create(
            title="Python",
            text="Repeat Django forms",
            reminder=timezone.now(),
            category=self.category,
        )

    def test_note_form_saves_note(self):
        form = NoteForm(
            data={
                "title": "New note",
                "text": "Create note from form",
                "reminder": "",
                "category": self.category.id,
            }
        )

        self.assertTrue(form.is_valid())
        note = form.save()

        self.assertEqual(note.title, "New note")
        self.assertEqual(note.text, "Create note from form")
        self.assertEqual(note.category, self.category)

    def test_note_form_updates_note(self):
        form = NoteForm(
            data={
                "title": "Updated title",
                "text": "Updated text",
                "reminder": "",
                "category": self.other_category.id,
            },
            instance=self.note,
        )

        self.assertTrue(form.is_valid())
        form.save()
        self.note.refresh_from_db()

        self.assertEqual(self.note.title, "Updated title")
        self.assertEqual(self.note.text, "Updated text")
        self.assertEqual(self.note.category, self.other_category)

    def test_create_note_view_saves_note(self):
        response = self.client.post(
            reverse("note_create"),
            {
                "title": "View note",
                "text": "Created by view",
                "reminder": "",
                "category": self.category.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Note.objects.filter(title="View note").exists())

    def test_detail_view_updates_note(self):
        response = self.client.post(
            reverse("note_detail", args=[self.note.pk]),
            {
                "title": "Changed from detail",
                "text": "Changed text",
                "reminder": "",
                "category": self.other_category.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, "Changed from detail")
        self.assertEqual(self.note.category, self.other_category)


class NotesApiIntegrationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Study")
        self.other_category = Category.objects.create(title="Work")
        self.note = Note.objects.create(
            title="API note",
            text="Created before API tests",
            category=self.category,
        )

    def test_api_notes_list_returns_notes(self):
        response = self.client.get(reverse("notes_api_list"))
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("notes", data)
        self.assertTrue(any(note["title"] == "API note" for note in data["notes"]))

    def test_api_note_detail_returns_note(self):
        response = self.client.get(reverse("note_api_detail", args=[self.note.pk]))
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["title"], "API note")
        self.assertEqual(data["category"]["title"], "Study")

    def test_api_create_note_saves_note(self):
        payload = {
            "title": "API created note",
            "text": "Created through JSON API",
            "reminder": None,
            "category_id": self.category.id,
        }

        response = self.client.post(
            reverse("note_api_create"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data["title"], "API created note")
        self.assertTrue(Note.objects.filter(title="API created note").exists())

    def test_api_update_note_changes_note(self):
        payload = {
            "title": "API updated note",
            "text": "Updated through JSON API",
            "reminder": None,
            "category_id": self.other_category.id,
        }

        response = self.client.post(
            reverse("note_api_update", args=[self.note.pk]),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, "API updated note")
        self.assertEqual(self.note.text, "Updated through JSON API")
        self.assertEqual(self.note.category, self.other_category)

    def test_api_create_note_with_wrong_json_returns_error(self):
        response = self.client.post(
            reverse("note_api_create"),
            data="wrong json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
