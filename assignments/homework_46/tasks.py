from celery import shared_task
from asgiref.sync import async_to_sync
from .models import Note
from .telegram_utils import send_telegram_message
@shared_task
def send_reminder_telegram_task(note_id):
    """Фонове завдання для відправки нагадування нотатки."""
    try:
        note = Note.objects.select_related('category', 'user').get(id=note_id)

        text = (
            f"⏰ <b>НАГАДУВАННЯ: {note.title}</b>\n\n"
            f"{note.text}\n\n"
            f"📁 Категорія: {note.category.title}"
        )
        # Викликаємо асинхронну функцію в синхронному Celery таску
        async_to_sync(send_telegram_message)(text)
        return f"Нагадування для нотатки {note_id} успішно надіслано."
    except Note.DoesNotExist:
        return f"Нотатка {note_id} не знайдена."