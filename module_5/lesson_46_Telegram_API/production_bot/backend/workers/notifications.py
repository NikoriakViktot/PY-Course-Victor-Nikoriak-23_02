"""
Background Worker — фонові завдання через asyncio.

У великих системах замінити на Celery + Redis/RabbitMQ.
Тут: простий asyncio.create_task() для демонстрації патерну.

Приклад real-world задач:
  - Надіслати нагадування про закінчення підписки за 3 дні
  - Щоденний звіт адміністратору
  - Очищення застарілих записів у БД
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot

logger = logging.getLogger(__name__)


async def subscription_expiry_notifier(bot: Bot) -> None:
    """Щогодини перевіряє підписки що закінчуються через 3 дні."""
    while True:
        try:
            await _check_expiring_subscriptions(bot)
        except Exception as e:
            logger.error("subscription_expiry_notifier error: %s", e)
        await asyncio.sleep(3600)  # кожну годину


async def _check_expiring_subscriptions(bot: Bot) -> None:
    from backend.core.database import AsyncSessionFactory
    from sqlalchemy import select
    from backend.models.subscription import Subscription
    from backend.models.user import User

    expires_threshold = datetime.now(timezone.utc) + timedelta(days=3)

    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(Subscription, User)
            .join(User, User.id == Subscription.user_id)
            .where(
                Subscription.expires_at <= expires_threshold,
                Subscription.tier != "free",
            )
        )
        rows = result.all()

    for sub, user in rows:
        days_left = (sub.expires_at - datetime.now(timezone.utc)).days
        try:
            await bot.send_message(
                user.tg_id,
                f"⚠️ Ваша підписка <b>{sub.tier}</b> закінчується через {days_left} дн.\n"
                f"Використайте /subscribe для продовження.",
            )
            logger.info("Нагадування надіслано: tg_id=%s tier=%s", user.tg_id, sub.tier)
        except Exception as e:
            logger.warning("Не вдалося надіслати нагадування tg_id=%s: %s", user.tg_id, e)
