from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import CHANNEL_ID
from database import mark_as_sent, get_pending_scheduled_notes

KYIV_TIMEZONE = ZoneInfo("Europe/Kyiv")

scheduler = AsyncIOScheduler(timezone=KYIV_TIMEZONE)


async def send_scheduled_note(bot, note_id: int, text: str):
    await bot.send_message(CHANNEL_ID, text)
    mark_as_sent(note_id)


def schedule_note(bot, note_id: int, text: str, send_at: datetime):
    scheduler.add_job(
        send_scheduled_note,
        trigger="date",
        run_date=send_at,
        args=[bot, note_id, text],
        id=f"note_{note_id}",
        replace_existing=True
    )


def load_saved_schedules(bot):
    now = datetime.now(KYIV_TIMEZONE)

    for note_id, text, send_at_str in get_pending_scheduled_notes():
        send_at = datetime.fromisoformat(send_at_str)

        if send_at > now:
            schedule_note(bot, note_id, text, send_at)