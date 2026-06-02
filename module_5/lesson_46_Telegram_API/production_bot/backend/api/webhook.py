"""
Webhook endpoint для Telegram.

ЧОМУ webhook секрет у URL?
  Telegram надсилає запити на /webhook/{SECRET}.
  Якщо хтось знає URL — він може надсилати фейкові Updates.
  Секрет у path = security through obscurity + перевірка X-Telegram-Bot-Api-Secret-Token.

ЧОМУ FastAPI а не просто aiogram?
  FastAPI надає:
    - Admin API (/admin/*)
    - Health check (/health)
    - Prometheus metrics (/metrics)
    - Swagger документацію (/docs)
  aiogram один не може це все.
"""
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Request, HTTPException

from backend.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def setup_webhook_router(bot: Bot, dp: Dispatcher) -> APIRouter:
    @router.post(settings.WEBHOOK_PATH)
    async def handle_webhook(request: Request) -> dict:
        # Перевіряємо секретний заголовок від Telegram
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_header != settings.WEBHOOK_SECRET:
            logger.warning("Webhook: невірний секрет від %s", request.client.host)
            raise HTTPException(status_code=403, detail="Invalid webhook secret")

        data = await request.json()
        update = Update(**data)

        # Передаємо Update у Dispatcher — він маршрутизує до handlers
        await dp.feed_update(bot=bot, update=update)
        return {"ok": True}

    return router
