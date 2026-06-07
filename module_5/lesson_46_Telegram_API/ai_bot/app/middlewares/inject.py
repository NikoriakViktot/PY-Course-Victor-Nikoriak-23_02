"""
app/middlewares/inject.py — Middleware для ін'єкції залежностей.

РОЛЬ У АРХІТЕКТУРІ:
    InjectMiddleware реалізує патерн Dependency Injection (DI):
        Handler декларує що йому потрібно (параметри функції).
        Middleware готує ці залежності (додає у data словник).
        aiogram з'єднує їх (передає data у handler).

    Без DI кожен handler мав би явно імпортувати Redis і створювати репозиторії:
        # ❌ БЕЗ DI — кожен handler знає деталі інфраструктури:
        async def handle_message(message):
            redis = aioredis.Redis(host="localhost", ...)
            history_repo = HistoryRepository(redis)
            history = await history_repo.get(...)

    З DI handler просто оголошує потрібні типи:
        # ✅ З DI — handler знає ТІЛЬКИ про бізнес-логіку:
        async def handle_message(message, history_repo: HistoryRepository):
            history = await history_repo.get(...)

ЯК AIOGRAM ПЕРЕДАЄ data В HANDLER:
    aiogram інспектує сигнатуру handler:
        async def cmd_reset(message: Message, history_repo: HistoryRepository)
                                              ^^^^^^^^^^^^
    Знаходить параметр "history_repo", шукає "history_repo" у data словнику,
    і передає знайдене значення у handler автоматично.

INNER vs OUTER:
    InjectMiddleware реєструється як INNER middleware (dp.message.middleware).

    Inner middleware виконується ПІСЛЯ маршрутизації роутерами.
    Тобто aiogram вже знає, який конкретний handler буде викликано.
    Це означає: залежності додаються лише для підходящих Updates.

    Outer middleware виконується ДО маршрутизації.
    Використовується для: rate limiting, блокування, глобальних перевірок.

ЩО ДОДАЄТЬСЯ У data:
    data["history_repo"] → HistoryRepository
        Потрібен handlers: cmd_start, cmd_reset, cmd_stats, cmd_history, handle_message

    data["redis"] → aioredis.Redis
        Потрібен: handle_message (для Circuit Breaker у ai_service)
        Чому не history_repo?  Бо Circuit Breaker записує власні ключі
        (ai_bot:cb:failures, ai_bot:cb:open) напряму у Redis, минаючи репозиторій.
"""
import redis.asyncio as aioredis
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.repositories.history_repo import HistoryRepository


class InjectMiddleware(BaseMiddleware):
    """
    Middleware для ін'єкції залежностей у handlers через data словник.

    Отримує залежності при ініціалізації (в bot.py),
    і додає їх у кожен Update при виконанні.
    """

    def __init__(
        self,
        history_repo: HistoryRepository,
        redis_client: aioredis.Redis,
    ) -> None:
        """
        Зберігає залежності при створенні middleware.

        Чому зберігаємо у __init__, а не створюємо у __call__?
            Якщо б ми створювали HistoryRepository у кожному __call__,
            то для кожного Update створювався б новий об'єкт — зайво.
            Один об'єкт на весь lifetime middleware — правильно.

        history_repo — один на весь Dispatcher (stateless: лише методи)
        redis_client — один пул з'єднань на весь Dispatcher
        """
        # Зберігаємо з підкресленням _ — convention для "private" атрибутів
        self._history_repo = history_repo
        self._redis = redis_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Викликається для кожного Update, що пройшов маршрутизацію.

        Параметри (aiogram передає автоматично):
            handler — наступний у ланцюгу: або інший middleware, або кінцевий handler
            event   — TelegramObject (найчастіше Message)
            data    — словник, який aiogram передасть у handler як kwargs

        Як middleware-ланцюг працює:
            Middleware викликає handler(event, data), тим самим "пропускаючи"
            Update далі по ланцюгу. Якщо не викликати handler — Update зупиниться.

            Послідовність:
                __call__() → data["history_repo"] = ... → await handler(event, data)
                                                                ↑
                                                    наступний middleware або кінцевий handler
        """
        # Додаємо HistoryRepository у data.
        # Handler оголошує: history_repo: HistoryRepository — aiogram передасть сюди.
        data["history_repo"] = self._history_repo

        # Додаємо Redis клієнт у data.
        # Handler (chat.py) оголошує: redis: aioredis.Redis
        # Використовується у ai_service.ask(redis_client=redis) для Circuit Breaker.
        data["redis"] = self._redis  # для Circuit Breaker у ai_service

        # Передаємо управління далі по ланцюгу middleware → кінцевий handler.
        # return — щоб повернути результат handler вгору по стеку викликів.
        return await handler(event, data)
