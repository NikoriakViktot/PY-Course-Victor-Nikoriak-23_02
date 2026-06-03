"""
app/handlers/chat.py — Головний AI Chat Handler.

РОЛЬ У АРХІТЕКТУРІ:
    Цей файл — серце бота. Тут відбувається основна взаємодія:
    текстове повідомлення від користувача → AI-відповідь.

ПОВНИЙ ПОТІК ВИКОНАННЯ (6 кроків):
  1. history_repo.append("user", text)    → зберігаємо у Redis
  2. bot.send_chat_action("typing")       → показуємо "Бот друкує..."
  3. history_repo.get(user_id)            → завантажуємо повну историю
  4. ai_service.ask(messages, redis)      → запит до Google Gemini
  5. history_repo.append("assistant", r)  → зберігаємо відповідь AI
  6. message.answer(chunk)               → надсилаємо відформатовану відповідь

FORMATTER LAYER:
    Відповідь Gemini містить Markdown синтаксис:
        ```python ... ```   — блоки коду
        **жирний**          — жирний текст
        *курсив*            — курсив
        - список            — маркований список

    Telegram розуміє HTML, але НЕ Markdown.
    format_ai_response() перетворює Markdown → Telegram HTML.
    split_long_message() розбиває довгі відповіді на частини до 4000 символів.

ROUTING PRIORITY:
    chat.router реєструється ОСТАННІМ у Dispatcher (bot.py).
    F.text перехоплює БУДЬ-ЯКИЙ текст.
    Конкретні команди (/start, /reset тощо) обробляються у commands.router
    (зареєстрований першим) — тому вони ніколи не потрапляють сюди.
"""
import logging
import redis.asyncio as aioredis

from aiogram import Router, F, Bot
from aiogram.types import Message

from app.repositories.history_repo import HistoryRepository
from app.services import ai_service

# Formatter utilities:
#   format_ai_response() — Markdown → Telegram HTML + шапка "🧠 AI Assistant"
#   split_long_message() — розбиває текст на чанки до MAX_MESSAGE_LEN символів
from app.utils.formatter import (
    format_ai_response,
    split_long_message,
)

# Logger для цього модуля
logger = logging.getLogger(__name__)

# Router — контейнер handlers.
# name="chat" видно у логах aiogram при дебагінгу маршрутизації.
router = Router(name="chat")


# =========================================================
# ГОЛОВНИЙ AI HANDLER
# =========================================================
# F.text — фільтр aiogram:
#   TRUE  — message.text is not None (є текстове повідомлення)
#   FALSE — фото, стікер, документ, голос тощо
#
# Завдяки цьому filter handler не викличеться для нетекстових Updates.
@router.message(F.text)
async def handle_message(
    message: Message,
    bot: Bot,
    history_repo: HistoryRepository,
    redis: aioredis.Redis,
) -> None:
    """
    Обробляє текстові повідомлення і генерує AI-відповідь.

    Параметри (Dependency Injection від aiogram + InjectMiddleware):
        message      — aiogram Message об'єкт (автоматично з aiogram)
        bot          — aiogram Bot клієнт (для send_chat_action)
        history_repo — HistoryRepository (з InjectMiddleware через data["history_repo"])
        redis        — aioredis.Redis клієнт (з InjectMiddleware через data["redis"])

    Повертає None — відповідь надсилається через message.answer() всередині.
    """

    # ── Підготовка даних ───────────────────────────────────────────────
    user_id = message.from_user.id
    # strip() прибирає пробіли і переноси рядків на початку/кінці тексту
    user_text = message.text.strip()

    # Ігноруємо порожні повідомлення (наприклад, лише пробіли чи переноси)
    if not user_text:
        return

    logger.info(
        "Запит від user_id=%s: %d chars",
        user_id,
        len(user_text),
    )

    # ── КРОК 1: Зберігаємо повідомлення user у Redis ──────────────────
    # Зберігаємо ДО запиту до AI — щоб AI мав повний контекст.
    # append() додає: {"role": "user", "content": user_text}
    # у JSON-список в Redis (ключ "history:{user_id}").
    await history_repo.append(user_id, "user", user_text)

    # ── КРОК 2: UX — показуємо "Бот друкує..." ────────────────────────
    # send_chat_action("typing"):
    #   Telegram показує "Andriuk bot is typing..." у шапці чату.
    #   Ефект зникає через ~5 сек або при надходженні нового повідомлення.
    #   Важливо для UX: без цього здається, що бот завис під час довгого запиту.
    #
    # Використовуємо bot.send_chat_action (не message.answer),
    # бо нам не потрібен Message у відповідь — лише side effect.
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # ── КРОК 3: Завантажуємо повну историю розмови ────────────────────
    # history — список [{role, content}, ...] з Redis.
    # Включає щойно збережене повідомлення (крок 1).
    # Максимум HISTORY_MAX_MESSAGES повідомлень (HistoryRepository обрізає автоматично).
    history = await history_repo.get(user_id)

    # ── КРОК 4: Запит до Google Gemini через fault-tolerant gateway ─────
    # ai_service.ask() виконує:
    #   1. Перевіряє Circuit Breaker (redis) — якщо open, повертає помилку
    #   2. Будує prompt з историї
    #   3. Спробує MODEL_POOL[0] (gemini-2.5-flash)
    #   4. При помилці (503/429/timeout) → MODEL_POOL[1] і т.д.
    #   5. Повертає текст відповіді або None при повній відмові
    #
    # redis_client передаємо для Circuit Breaker:
    #   При 5 збоях підряд → circuit відкривається на 5 хв.
    #   Нові запити отримують повідомлення про недоступність без виклику API.
    response_text = await ai_service.ask(
        messages=history,
        redis_client=redis,
    )

    # ── КРОК 4.5: Перевірка відповіді ────────────────────────────────
    # None = всі моделі у MODEL_POOL вичерпані і не відповіли.
    # Повідомляємо користувача і виходимо БЕЗ збереження у историю.
    if response_text is None:
        await message.answer(
            "😔 AI сервіс недоступний. Спробуйте /reset та повторіть запит."
        )
        return

    # ── КРОК 5: Зберігаємо відповідь AI у историю ────────────────────
    # Зберігаємо лише якщо отримали відповідь (не None).
    # append() додає: {"role": "assistant", "content": response_text}
    await history_repo.append(user_id, "assistant", response_text)

    # ── КРОК 6: Formatter Layer → Telegram UI ────────────────────────
    # Gemini повертає Markdown. Telegram розуміє HTML.
    # format_ai_response():
    #   ```python...``` → <pre><code class="language-python">...</code></pre>
    #   **жирний**      → <b>жирний</b>
    #   *курсив*        → <i>курсив</i>
    #   `inline code`   → <code>inline code</code>
    #   - пункт         → • пункт
    #   + додає шапку "🧠 AI Assistant" і горизонтальну лінію
    formatted_response = format_ai_response(response_text)

    # split_long_message():
    #   Telegram ліміт = 4096 символів на повідомлення.
    #   Якщо відповідь довша — розбиваємо на чанки по MAX_MESSAGE_LEN символів.
    #   Повертає список рядків: ["частина 1", "частина 2", ...]
    chunks = split_long_message(formatted_response)

    # Надсилаємо кожен чанк окремим повідомленням
    for chunk in chunks:
        try:
            # HTML parse mode активний глобально через DefaultBotProperties
            await message.answer(chunk)

        except Exception:
            # Якщо Telegram не зміг відрендерити HTML (наприклад, незакритий тег)
            # — логуємо помилку і надсилаємо повідомлення про помилку форматування.
            logger.exception("Telegram render error")
            await message.answer("❌ Помилка форматування відповіді.")


# =========================================================
# FALLBACK HANDLER ДЛЯ НЕ-ТЕКСТОВИХ ПОВІДОМЛЕНЬ
# =========================================================
# @router.message() без фільтрів — catch-all для ВСЬОГО,
# що не перехопив F.text handler вище (фото, стікери, голос, файли).
#
# Реєструється ПІСЛЯ F.text handler — тому не конкурує з ним.
@router.message()
async def handle_non_text(message: Message) -> None:
    """
    Повідомляє користувача, що нетекстовий контент не підтримується.

    Без цього handler aiogram просто мовчки ігнорував би нетекстові Updates.
    Явне повідомлення — краще UX.
    """
    await message.answer("Я розумію лише текст. Надішли текстове повідомлення!")
