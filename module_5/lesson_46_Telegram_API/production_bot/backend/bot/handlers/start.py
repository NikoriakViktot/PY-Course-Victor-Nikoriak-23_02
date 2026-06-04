import logging
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from backend.services.user_service import UserService
from backend.core.database import AsyncSessionFactory

logger = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user

    # Парсимо реферальний код з deep link: /start ref_123456789
    referrer_tg_id: int | None = None
    if message.text and " " in message.text:
        arg = message.text.split(" ", 1)[1]
        if arg.startswith("ref_"):
            try:
                referrer_tg_id = int(arg.replace("ref_", ""))
            except ValueError:
                pass

    async with AsyncSessionFactory() as session:
        service = UserService(session)
        _, is_new = await service.register_or_get(
            tg_id=user.id,
            first_name=user.first_name,
            username=user.username,
            language_code=user.language_code,
            referrer_tg_id=referrer_tg_id,
        )
        await session.commit()

    if is_new:
        await message.answer(
            f"Вітаємо, <b>{user.first_name}</b>! 🎉\n\n"
            f"Ви отримали безкоштовний план (10 запитів).\n"
            f"Використайте /subscribe для оновлення.",
        )
    else:
        await message.answer(f"З поверненням, <b>{user.first_name}</b>! 👋")


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message) -> None:
    await message.answer(
        "<b>Плани підписки:</b>\n\n"
        "🆓 <b>Free</b> — 10 запитів (безкоштовно)\n"
        "⚡ <b>Basic</b> — 50 запитів / 30 днів\n"
        "💎 <b>Premium</b> — безліміт / 30 днів\n\n"
        "Для оплати зверніться до підтримки або адміністратора."
    )
