import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Category, Note
from .telegram import (
    TelegramBotClient,
    TelegramResult,
    create_note_from_telegram_text,
    format_note_message,
    handle_telegram_update,
    parse_telegram_note_payload,
)

User = get_user_model()


class AuthenticatedNotesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="olena", password="pass12345")
        self.other_user = User.objects.create_user(
            username="taras", password="pass12345"
        )
        self.group = Group.objects.create(name="Команда")
        self.group.user_set.add(self.user, self.other_user)
        self.client.force_login(self.user)


class NotesModelTests(TestCase):
    def test_category_and_note_string_representations(self):
        user = User.objects.create_user(username="olena", password="pass12345")
        category = Category.objects.create(title="Навчання")
        note = Note.objects.create(
            title="Повторити Django",
            text="Форми, моделі та маршрути",
            category=category,
            owner=user,
        )

        self.assertEqual(str(category), "Навчання")
        self.assertEqual(str(note), "Повторити Django")
        self.assertEqual(
            note.get_absolute_url(), reverse("note_detail", kwargs={"note_id": note.id})
        )


class NotePersistenceUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="olena", password="pass12345")
        self.personal = Category.objects.create(title="Особисте")
        self.work = Category.objects.create(title="Робота")

    def test_save_note_persists_fields_and_timestamps(self):
        reminder = timezone.now() + timezone.timedelta(hours=2)

        note = Note.objects.create(
            title="Купити продукти",
            text="Молоко, хліб, сир",
            category=self.personal,
            reminder=reminder,
            owner=self.user,
        )

        saved_note = Note.objects.get(id=note.id)
        self.assertEqual(saved_note.title, "Купити продукти")
        self.assertEqual(saved_note.text, "Молоко, хліб, сир")
        self.assertEqual(saved_note.category, self.personal)
        self.assertEqual(saved_note.owner, self.user)
        self.assertIsNone(saved_note.group)
        self.assertEqual(saved_note.reminder, reminder)
        self.assertIsNotNone(saved_note.created_at)
        self.assertIsNotNone(saved_note.updated_at)

    def test_change_note_persists_updated_fields(self):
        note = Note.objects.create(
            title="Стара назва",
            text="Старий текст",
            category=self.personal,
            owner=self.user,
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
        self.assertEqual(changed_note.owner, self.user)
        self.assertEqual(changed_note.reminder, new_reminder)
        self.assertEqual(changed_note.created_at, created_at)
        self.assertGreaterEqual(changed_note.updated_at, created_at)


class AuthenticationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="olena", password="pass12345")

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Вхід користувача")

    def test_notes_list_requires_login(self):
        response = self.client.get(reverse("notes_list"))

        self.assertRedirects(
            response, f'{reverse("login")}?next={reverse("notes_list")}'
        )

    def test_logout_requires_post_and_logs_user_out(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        response = self.client.get(reverse("notes_list"))
        self.assertRedirects(
            response, f'{reverse("login")}?next={reverse("notes_list")}'
        )


class NotesViewTests(AuthenticatedNotesTestCase):
    def setUp(self):
        super().setUp()
        self.study = Category.objects.create(title="Навчання")
        self.work = Category.objects.create(title="Робота")
        self.note = Note.objects.create(
            title="Django форми",
            text="Потрібно повторити ModelForm",
            category=self.study,
            reminder=timezone.now() + timezone.timedelta(days=1),
            owner=self.user,
        )
        self.other_note = Note.objects.create(
            title="Зустріч",
            text="Обговорити задачі команди",
            category=self.work,
            owner=self.other_user,
        )
        self.group_note = Note.objects.create(
            title="План команди",
            text="Спільна нотатка для групи",
            category=self.work,
            owner=self.other_user,
            group=self.group,
        )

    def test_notes_list_renders_only_current_user_notes(self):
        response = self.client.get(reverse("notes_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django форми")
        self.assertNotContains(response, "Зустріч")
        self.assertNotContains(response, "План команди")

    def test_notes_list_can_switch_to_group_notes(self):
        response = self.client.get(reverse("notes_list"), {"scope": "group"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "План команди")
        self.assertNotContains(response, "Django форми")
        self.assertContains(response, "Нотатки групи")

    def test_notes_list_filters_by_text_query(self):
        response = self.client.get(reverse("notes_list"), {"query": "ModelForm"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django форми")
        self.assertNotContains(response, "Зустріч")

    def test_notes_list_filters_by_category(self):
        own_work_note = Note.objects.create(
            title="План спринту",
            text="Підготувати задачі",
            category=self.work,
            owner=self.user,
        )

        response = self.client.get(reverse("notes_list"), {"category": self.work.id})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own_work_note.title)
        self.assertNotContains(response, "Django форми")
        self.assertNotContains(response, "Зустріч")

    def test_note_create_sets_current_user(self):
        response = self.client.post(
            reverse("note_create"),
            {
                "title": "Нова нотатка",
                "text": "Текст нової нотатки",
                "category": self.study.id,
                "reminder": "",
                "group": self.group.id,
            },
        )

        note = Note.objects.get(title="Нова нотатка")
        self.assertEqual(note.owner, self.user)
        self.assertEqual(note.group, self.group)
        self.assertRedirects(response, note.get_absolute_url())

    def test_note_update_allows_only_owner(self):
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

        response = self.client.post(
            reverse("note_detail", kwargs={"note_id": self.other_note.id}),
            {
                "title": "Чужа нотатка",
                "text": self.other_note.text,
                "category": self.other_note.category.id,
                "reminder": "",
            },
        )
        self.assertEqual(response.status_code, 404)
        self.other_note.refresh_from_db()
        self.assertEqual(self.other_note.title, "Зустріч")

    def test_group_note_is_readable_but_not_editable_by_group_member(self):
        response = self.client.get(
            reverse("note_detail", kwargs={"note_id": self.group_note.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "План команди")
        self.assertContains(response, "Перегляд групової нотатки")

        response = self.client.post(
            reverse("note_detail", kwargs={"note_id": self.group_note.id}),
            {
                "title": "Не можна змінити",
                "text": self.group_note.text,
                "category": self.group_note.category.id,
                "group": self.group.id,
                "reminder": "",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.group_note.refresh_from_db()
        self.assertEqual(self.group_note.title, "План команди")

    def test_note_delete_requires_post_and_allows_only_owner(self):
        get_response = self.client.get(
            reverse("note_delete", kwargs={"note_id": self.note.id})
        )
        self.assertRedirects(get_response, self.note.get_absolute_url())
        self.assertTrue(Note.objects.filter(id=self.note.id).exists())

        other_response = self.client.post(
            reverse("note_delete", kwargs={"note_id": self.other_note.id})
        )
        self.assertEqual(other_response.status_code, 404)
        self.assertTrue(Note.objects.filter(id=self.other_note.id).exists())

        post_response = self.client.post(
            reverse("note_delete", kwargs={"note_id": self.note.id})
        )
        self.assertRedirects(post_response, reverse("notes_list"))
        self.assertFalse(Note.objects.filter(id=self.note.id).exists())


class CategoryViewTests(AuthenticatedNotesTestCase):
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


class NoteApiIntegrationTests(AuthenticatedNotesTestCase):
    def setUp(self):
        super().setUp()
        self.study = Category.objects.create(title="Навчання")
        self.work = Category.objects.create(title="Робота")
        self.note = Note.objects.create(
            title="Початкова нотатка",
            text="Початковий текст",
            category=self.study,
            owner=self.user,
        )
        self.other_note = Note.objects.create(
            title="Чужа нотатка",
            text="Початковий текст",
            category=self.study,
            owner=self.other_user,
        )
        self.group_note = Note.objects.create(
            title="Групова API нотатка",
            text="Доступна учасникам групи",
            category=self.work,
            owner=self.other_user,
            group=self.group,
        )

    def test_api_lists_only_current_user_notes_with_test_client(self):
        response = self.client.get(reverse("api_notes"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["notes"]), 1)
        self.assertEqual(data["notes"][0]["title"], "Початкова нотатка")
        self.assertEqual(data["notes"][0]["category"], self.study.id)
        self.assertEqual(data["notes"][0]["owner"], self.user.id)

        def test_api_lists_group_notes_with_test_client(self):
            response = self.client.get(reverse("api_notes"), {"scope": "group"})

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(len(data["notes"]), 1)
            self.assertEqual(data["notes"][0]["title"], "Групова API нотатка")
            self.assertEqual(data["notes"][0]["group"], self.group.id)

    def test_api_creates_note_with_test_client(self):
        payload = {
            "title": "API нотатка",
            "text": "Створено через JSON API",
            "category": self.work.id,
            "reminder": "2026-06-01T09:30",
            "group": self.group.id,
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
        self.assertEqual(note.owner, self.user)
        self.assertEqual(note.group, self.group)

    def test_api_updates_only_current_user_note_with_test_client(self):
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

        response = self.client.patch(
            reverse("api_note_detail", kwargs={"note_id": self.other_note.id}),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            reverse("api_note_detail", kwargs={"note_id": self.group_note.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["note"]["title"], "Групова API нотатка")

        response = self.client.patch(
            reverse("api_note_detail", kwargs={"note_id": self.group_note.id}),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_api_returns_validation_errors_for_invalid_create_payload(self):
        response = self.client.post(
            reverse("api_notes"),
            data=json.dumps({"title": "Без категорії"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())
        self.assertFalse(Note.objects.filter(title="Без категорії").exists())


class TelegramIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="olena", password="pass12345")
        self.category = Category.objects.create(title="Навчання")

    def test_parse_telegram_note_command_with_reminder(self):
        payload = parse_telegram_note_payload(
            "/note Навчання | Telegram бот | Зробити ДЗ | 2026-06-10 14:30"
        )

        self.assertEqual(payload.category_title, "Навчання")
        self.assertEqual(payload.title, "Telegram бот")
        self.assertEqual(payload.text, "Зробити ДЗ")
        self.assertIsNotNone(payload.reminder)

    def test_create_note_from_plain_telegram_text_uses_default_category(self):
        note = create_note_from_telegram_text("Швидка нотатка з Telegram")

        self.assertEqual(note.category.title, "Telegram")
        self.assertEqual(note.title, "Швидка нотатка з Telegram")
        self.assertEqual(note.text, "Швидка нотатка з Telegram")

    def test_handle_telegram_update_creates_note_and_replies(self):
        class FakeClient:
            channel_id = "@notes"

            def __init__(self):
                self.messages = []

            def send_message(self, text):
                self.messages.append(("channel", text))
                return TelegramResult(sent=True)

            def send_chat_message(self, chat_id, text):
                self.messages.append((chat_id, text))
                return TelegramResult(sent=True)

        client = FakeClient()
        update = {
            "update_id": 1,
            "message": {
                "chat": {"id": 123},
                "text": "/note Робота | Зустріч | Підготувати порядок денний",
            },
        }

        handled = handle_telegram_update(update, client=client)

        note = Note.objects.get(title="Зустріч")
        self.assertTrue(handled)
        self.assertEqual(note.category.title, "Робота")
        self.assertIsNotNone(note.telegram_sent_at)
        self.assertEqual(client.messages[0][0], "channel")
        self.assertEqual(client.messages[1][0], 123)

    def test_handle_telegram_update_returns_categories(self):
        class FakeClient:
            def __init__(self):
                self.messages = []

            def send_chat_message(self, chat_id, text):
                self.messages.append((chat_id, text))
                return TelegramResult(sent=True)

        client = FakeClient()
        update = {"message": {"chat": {"id": 123}, "text": "/categories"}}

        handled = handle_telegram_update(update, client=client)

        self.assertTrue(handled)
        self.assertIn("Навчання", client.messages[0][1])

    def test_format_note_message_contains_note_details(self):
        reminder = timezone.now() + timezone.timedelta(hours=1)
        note = Note.objects.create(
            title="Telegram нотатка",
            text="Надіслати в канал",
            category=self.category,
            reminder=reminder,
            owner=self.user,
        )

        message = format_note_message(note)

        self.assertIn("Нова нотатка", message)
        self.assertIn("Telegram нотатка", message)
        self.assertIn("Навчання", message)
        self.assertIn("olena", message)

    @override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHANNEL_ID="")
    def test_telegram_client_skips_when_not_configured(self):
        result = TelegramBotClient().send_message("test")

        self.assertFalse(result.sent)
        self.assertTrue(result.skipped)

    def test_created_note_is_published_from_web_form(self):
        self.client.force_login(self.user)

        class FakeClient:
            def send_message(self, text):
                return TelegramResult(sent=True)

        from .telegram import publish_created_note

        note = Note.objects.create(
            title="Чернетка",
            text="Текст",
            category=self.category,
            owner=self.user,
        )
        result = publish_created_note(note, client=FakeClient())

        note.refresh_from_db()
        self.assertTrue(result.sent)
        self.assertIsNotNone(note.telegram_sent_at)

    def test_send_telegram_reminders_marks_due_notes(self):
        due_note = Note.objects.create(
            title="Нагадати зараз",
            text="Пора виконати задачу",
            category=self.category,
            reminder=timezone.now() - timezone.timedelta(minutes=5),
            owner=self.user,
        )
        future_note = Note.objects.create(
            title="Нагадати завтра",
            text="Ще не час",
            category=self.category,
            reminder=timezone.now() + timezone.timedelta(days=1),
            owner=self.user,
        )

        class FakeClient:
            def send_message(self, text):
                return TelegramResult(sent=True)

        from .telegram import publish_due_reminders

        sent_count, failed_count = publish_due_reminders(client=FakeClient())

        due_note.refresh_from_db()
        future_note.refresh_from_db()
        self.assertEqual(sent_count, 1)
        self.assertEqual(failed_count, 0)
        self.assertIsNotNone(due_note.reminder_telegram_sent_at)
        self.assertIsNone(future_note.reminder_telegram_sent_at)

    @override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHANNEL_ID="")
    def test_send_telegram_reminders_management_command_runs(self):
        Note.objects.create(
            title="Без налаштувань",
            text="Команда не падає без токена",
            category=self.category,
            reminder=timezone.now() - timezone.timedelta(minutes=5),
            owner=self.user,
        )

        call_command("send_telegram_reminders")

    @override_settings(TELEGRAM_BOT_TOKEN="")
    def test_run_telegram_bot_command_exits_without_token(self):
        call_command("run_telegram_bot", once=True)