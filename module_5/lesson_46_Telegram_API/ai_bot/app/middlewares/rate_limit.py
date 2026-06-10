"""
app/middlewares/rate_limit.py — Middleware для обмеження частоти запитів.

РОЛЬ У АРХІТЕКТУРІ:
    Захищає бота від спаму та зловживань.
    Якщо користувач надсилає забагато повідомлень — відхиляємо їх
    і відповідаємо "Забагато запитів!".

АЛГОРИТМ (Sliding Window Counter):
    При кожному повідомленні від user_id:
      1. Атомарно збільшуємо лічильник у Redis (INCR)
      2. Якщо це перший запит у вікні — встановлюємо TTL (EXPIRE)
      3. Якщо лічильник > RATE_LIMIT_REQUESTS — відхиляємо

    Приклад з дефолтними налаштуваннями (5 запитів / 60 сек):
        10:00:00 — 1-й запит → count=1, TTL=60 → OK ✓
        10:00:10 — 2-й запит → count=2         → OK ✓
        10:00:20 — 3-й запит → count=3         → OK ✓
        10:00:30 — 4-й запит → count=4         → OK ✓
        10:00:40 — 5-й запит → count=5         → OK ✓
        10:00:50 — 6-й запит → count=6         → BLOCKED ✗
        10:01:00 — TTL вичерпано → count видалено → ОК знову

OUTER vs INNER:
    RateLimitMiddleware реєструється як OUTER middleware:
        dp.message.outer_middleware(RateLimitMiddleware(rate_repo))

    Outer виконується ДО перевірки роутерів.
    Це критично: якщо б це був inner, то aiogram вже витратив би ресурси
    на маршрутизацію Update перед тим, як відхилити його.

    Outer може "вбити" Update достроково:
        return (без виклику handler) → Update відкинуто, Handler не викликається.

ВАЖЛИВА ДЕТАЛЬ — перевірка isinstance:
    TelegramObject може бути не тільки Message, але й CallbackQuery, InlineQuery тощо.
    Rate limiting застосовуємо ТІЛЬКИ до Message.
    Для інших типів Updates — пропускаємо без перевірки.
"""
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.repositories.rate_limit_repo import RateLimitRepository
from app.config import config

# Logger для цього модуля
logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """
    Outer middleware для обмеження частоти запитів від користувачів.

    Зберігає посилання на RateLimitRepository при ініціалізації.
    Використовує Redis (через repo) для атомарних операцій з лічильниками.
    """

    def __init__(self, rate_repo: RateLimitRepository) -> None:
        """
        Зберігає репозиторій для подальшого використання у __call__.

        rate_repo — stateless об'єкт (лише методи + посилання на Redis).
        Один екземпляр на весь Dispatcher — не потрібно створювати для кожного Update.
        """
        self._rate_repo = rate_repo

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Викликається для КОЖНОГО вхідного Update (outer middleware).

        Логіка:
            1. Якщо це не Message → пропустити без перевірки
            2. Якщо немає from_user → пропустити (системні повідомлення)
            3. Перевірити ліміт у Redis
            4. Якщо перевищено → відповісти і ЗУПИНИТИСЬ (return без handler)
            5. Якщо ок → передати далі (await handler)

        Параметри:
            handler — наступний у ланцюгу (inner middleware або handler)
            event   — поточний Update (Message, CallbackQuery тощо)
            data    — словник даних для handler
        """

        # ── Перевірка типу Update ────────────────────────────────────────
        # Rate limiting застосовуємо ЛИШЕ до Message (не до CallbackQuery тощо).
        # Якщо це не Message → пропускаємо без перевірки.
        if not isinstance(event, Message):
            return await handler(event, data)

        # ── Перевірка наявності відправника ─────────────────────────────
        # from_user може бути None для системних повідомлень (наприклад, pinned message).
        # В таких випадках rate limiting не потрібен → пропускаємо.
        user = event.from_user
        if not user:
            return await handler(event, data)

        # ── Основна перевірка ліміту ─────────────────────────────────────
        # check_and_increment():
        #   - Атомарно збільшує лічильник у Redis (INCR)
        #   - Повертає (is_allowed, current_count)
        #   - is_allowed = count <= RATE_LIMIT_REQUESTS
        is_allowed, count = await self._rate_repo.check_and_increment(user.id)

        # ── Блокування при перевищенні ───────────────────────────────────
        if not is_allowed:
            # Дізнаємось скільки секунд до скидання лічильника
            # (TTL ключа у Redis)
            ttl = await self._rate_repo.get_ttl(user.id)

            logger.warning(
                "Rate limit: user_id=%s count=%s",
                user.id,
                count,
            )

            # Відповідаємо повідомленням про блокування.
            # event.answer() — shortcut для відправки у той самий чат.
            await event.answer(
                f"⏳ Забагато запитів!\n"
                f"Ліміт: {config.RATE_LIMIT_REQUESTS} запитів "
                f"за {config.RATE_LIMIT_WINDOW} секунд.\n"
                f"Зачекайте {ttl} секунд."
            )

            # КРИТИЧНО: повертаємо None БЕЗ виклику handler.
            # Це зупиняє весь ланцюг middleware — Handler НЕ отримає цей Update.
            return

        # ── Пропускаємо далі ─────────────────────────────────────────────
        # Додаємо rate_repo у data (на випадок якщо handler захоче його використати)
        data["rate_repo"] = self._rate_repo

        # Передаємо управління далі по ланцюгу (inner middleware → handler)
        return await handler(event, data)
