"""
BlockCheck Middleware — перевіряє чи користувач не заблокований.

Outer middleware: виконується до будь-якого router/handler.
Заблокований user → Update відкидається мовчки.
"""
from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from backend.core.database import AsyncSessionFactory
from backend.repositories.user_repo import UserRepository


class BlockCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        if not user:
            return await handler(event, data)

        async with AsyncSessionFactory() as session:
            repo = UserRepository(session)
            db_user = await repo.get_by_tg_id(user.id)
            if db_user and db_user.is_blocked:
                return  # мовчки ігноруємо

        return await handler(event, data)
