"""Utilities for using Telegram as a notes bot and channel publisher.

The bot is configured through environment variables in ``notes_app.settings``.
Network calls are intentionally isolated here so views, commands and tests can
mock one small public API.
"""

from __future__ import annotations

import html
import json
import logging
from dataclasses import dataclass
from urllib import error, request

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Category, Note

logger = logging.getLogger(__name__)

HELP_TEXT = """Вітаю! Я бот нотаток.

Команди:
/start або /help — показати підказку
/categories — показати категорії
/note Категорія | Назва | Текст | 2026-06-10 14:30 — створити нотатку з нагадуванням
/note Категорія | Назва | Текст — створити нотатку без нагадування

Також можна надіслати будь-який текст без команди — він стане нотаткою в категорії Telegram."""


@dataclass(frozen=True)
class TelegramResult:
    """Result of a Telegram Bot API operation."""

    sent: bool
    skipped: bool = False
    reason: str = ""


@dataclass(frozen=True)
class TelegramNotePayload:
    """Parsed note data received from a Telegram chat."""

    category_title: str
    title: str
    text: str
    reminder: object | None = None


class TelegramBotClient:
    """Small Telegram Bot API client based on Python's standard library."""

    def __init__(self, token: str | None = None, channel_id: str | None = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.channel_id = channel_id or settings.TELEGRAM_CHANNEL_ID

    @property
    def has_token(self) -> bool:
        return bool(self.token)

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.channel_id)

    def api_call(self, method: str, payload: dict | None = None) -> dict:
        if not self.has_token:
            return {"ok": False, "description": "TELEGRAM_BOT_TOKEN не налаштовано."}

        data = json.dumps(payload or {}).encode("utf-8")
        api_request = request.Request(
            f"https://api.telegram.org/bot{self.token}/{method}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(
                api_request, timeout=settings.TELEGRAM_TIMEOUT
            ) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, error.HTTPError, json.JSONDecodeError) as exc:
            logger.warning("Telegram API call %s failed: %s", method, exc)
            return {"ok": False, "description": str(exc)}

    def send_message(self, text: str) -> TelegramResult:
        """Send a message to the configured Telegram channel."""

        if not self.is_configured:
            return TelegramResult(
                sent=False,
                skipped=True,
                reason="TELEGRAM_BOT_TOKEN або TELEGRAM_CHANNEL_ID не налаштовано.",
            )

        return self.send_chat_message(self.channel_id, text)

    def send_chat_message(self, chat_id: int | str, text: str) -> TelegramResult:
        """Send a message to any Telegram chat id."""

        response_payload = self.api_call(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )
        if response_payload.get("ok"):
            return TelegramResult(sent=True)

        description = response_payload.get("description", "Telegram API error")
        logger.warning("Telegram API returned an error: %s", description)
        return TelegramResult(sent=False, skipped=not self.has_token, reason=description)

    def get_updates(
            self, offset: int | None = None, timeout: int | None = None
    ) -> list[dict]:
        """Read updates from the Telegram bot long-polling endpoint."""

        payload = {
            "timeout": settings.TELEGRAM_POLL_TIMEOUT if timeout is None else timeout,
            "allowed_updates": ["message"],
        }
        if offset is not None:
            payload["offset"] = offset

        response_payload = self.api_call("getUpdates", payload)
        if not response_payload.get("ok"):
            logger.warning(
                "Telegram getUpdates returned an error: %s",
                response_payload.get("description", "Telegram API error"),
            )
            return []
        return response_payload.get("result", [])


def format_note_message(note: Note, *, scheduled: bool = False) -> str:
    """Build a compact HTML message for a newly-created or scheduled note."""

    title = html.escape(note.title)
    text = html.escape(note.text)
    category = html.escape(note.category.title)
    owner = html.escape(note.owner.username) if note.owner else "Telegram bot"
    header = "⏰ Нагадування про нотатку" if scheduled else "📝 Нова нотатка"
    parts = [
        f"<b>{header}</b>",
        f"<b>{title}</b>",
        text,
        f"Категорія: {category}",
        f"Автор: {owner}",
    ]

    if note.group:
        parts.append(f"Група: {html.escape(note.group.name)}")
    if note.reminder:
        reminder_time = timezone.localtime(note.reminder)
        parts.append(f"Час нагадування: {reminder_time:%d.%m.%Y %H:%M}")

    return "\n".join(parts)


def parse_telegram_note_payload(message_text: str) -> TelegramNotePayload:
    """Parse a Telegram note command or plain text into note fields."""

    raw_text = message_text.strip()
    first_token = raw_text.split(maxsplit=1)[0] if raw_text else ""
    if first_token.split("@", 1)[0] == "/note":
        raw_text = raw_text.split(maxsplit=1)[1].strip() if " " in raw_text else ""

    parts = [part.strip() for part in raw_text.split("|")]
    if len(parts) < 3:
        default_category = settings.TELEGRAM_DEFAULT_CATEGORY
        title = parts[0][:80] if parts and parts[0] else "Нотатка з Telegram"
        return TelegramNotePayload(
            category_title=default_category,
            title=title,
            text=raw_text or "Нотатка з Telegram",
        )

    reminder = None
    if len(parts) >= 4 and parts[3]:
        reminder = parse_datetime(parts[3].replace(" ", "T", 1))
        if reminder and timezone.is_naive(reminder):
            reminder = timezone.make_aware(reminder, timezone.get_current_timezone())

    return TelegramNotePayload(
        category_title=parts[0] or settings.TELEGRAM_DEFAULT_CATEGORY,
        title=parts[1] or "Нотатка з Telegram",
        text=parts[2] or "-",
        reminder=reminder,
    )


def get_telegram_note_owner():
    """Return the optional Django user assigned as owner for bot-created notes."""

    username = settings.TELEGRAM_NOTE_OWNER_USERNAME
    if not username:
        return None
    User = get_user_model()
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        logger.warning("Telegram note owner %s does not exist.", username)
        return None


def create_note_from_telegram_text(message_text: str) -> Note:
    """Create a Django note from a Telegram message."""

    payload = parse_telegram_note_payload(message_text)
    category, _ = Category.objects.get_or_create(title=payload.category_title)
    return Note.objects.create(
        title=payload.title,
        text=payload.text,
        category=category,
        reminder=payload.reminder,
        owner=get_telegram_note_owner(),
    )


def handle_telegram_update(
    update: dict, client: TelegramBotClient | None = None
) -> bool:
    """Handle one Telegram update.

    Returns True when the update was recognized as a message for the bot.
    """

    client = client or TelegramBotClient()
    message = update.get("message") or {}
    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if not text or chat_id is None:
        return False

    command = text.split(maxsplit=1)[0].split("@", 1)[0]
    if command in {"/start", "/help"}:
        client.send_chat_message(chat_id, html.escape(HELP_TEXT))
        return True
    if command == "/categories":
        categories = Category.objects.order_by("title").values_list(
            "title", flat=True
        )
        category_list = "\n".join(f"• {html.escape(title)}" for title in categories)
        client.send_chat_message(chat_id, category_list or "Категорій поки що немає.")
        return True

    note = create_note_from_telegram_text(text)
    publish_result = publish_created_note(note, client=client)
    status = (
        "і переслано в канал"
        if publish_result.sent
        else "але канал не налаштовано"
    )
    client.send_chat_message(
        chat_id,
        f"✅ Нотатку <b>{html.escape(note.title)}</b> створено {status}.",
    )
    return True


def publish_created_note(
    note: Note, client: TelegramBotClient | None = None
) -> TelegramResult:
    """Send a newly-created note to the configured Telegram channel."""

    client = client or TelegramBotClient()
    result = client.send_message(format_note_message(note))
    if result.sent:
        note.telegram_sent_at = timezone.now()
        note.save(update_fields=["telegram_sent_at"])
    return result


def publish_due_reminders(client: TelegramBotClient | None = None) -> tuple[int, int]:
    """Send all due unsent note reminders.

    Returns ``(sent_count, skipped_or_failed_count)``.
    """

    client = client or TelegramBotClient()
    due_notes = Note.objects.select_related("category", "owner", "group").filter(
        reminder__lte=timezone.now(),
        reminder_telegram_sent_at__isnull=True,
    )

    sent_count = 0
    failed_count = 0
    for note in due_notes:
        result = client.send_message(format_note_message(note, scheduled=True))
        if result.sent:
            note.reminder_telegram_sent_at = timezone.now()
            note.save(update_fields=["reminder_telegram_sent_at"])
            sent_count += 1
        else:
            failed_count += 1

    return sent_count, failed_count