from .telegram_utils import send_telegram_message
from .tasks import send_reminder_telegram_task
# Всередині асинхронного main_page view, де обробляється POST-запит:
async def main_page(request):
    # ... попередній код фільтрації та отримання даних ...
    if request.method == 'POST':
        def handle_post():
            form = NoteForm(request.POST, user=request.user)
            if form.is_valid():
                note = form.save(commit=False)
                note.user = request.user
                note.save()
                return note
            return None
        new_note = await sync_to_async(handle_post)()
        if new_note:
            # Формуємо текст повідомлення для Telegram
            telegram_text = (
                f"📌 <b>Нова нотатка: {new_note.title}</b>\n\n"
                f"{new_note.text}\n\n"
                f"📁 Категорія: {new_note.category.title}\n"
                f"👤 Автор: {new_note.user.username}"
            )
            if new_note and new_note.reminder:
                # Перевіряємо, чи час нагадування в майбутньому
                if new_note.reminder > timezone.now():
                    send_reminder_telegram_task.apply_async(
                        args=[new_note.id],
                        eta=new_note.reminder  # Передаємо точний час, коли таск має виконатись
                    )
            # Відправляємо в канал (не блокуючи основний потік завдяки асинхронності)
            await send_telegram_message(telegram_text)
            return redirect('main_page')