"""
app/bot.py — Фабрики для Bot, Dispatcher, Redis + lifecycle-хуки.

РОЛЬ У АРХІТЕКТУРІ:
    Цей файл — "складальний цех" бота.
    Він не містить бізнес-логіки — лише збирає компоненти разом.

    Патерн "Factory Function":
        Замість глобальних об'єктів — функції, що повертають готові об'єкти.
        Переваги:
          - Легко тестувати (можна підмінити залежності)
          - Явний порядок ініціалізації
          - Немає прихованих залежностей на глобальні змінні

ПОРЯДОК РЕЄСТРАЦІЇ MIDDLEWARE:
    dp.message.outer_middleware(RateLimitMiddleware)  ← зовнішній (перший)
    dp.message.middleware(InjectMiddleware)            ← внутрішній (другий)

    Update → [outer: RateLimitMiddleware] → [inner: InjectMiddleware] → Handler

    Outer middleware:
        Виконується ДО перевірки роутерів.
        Може відкинути Update (return без виклику handler).
        Використовуємо для: rate limiting, блокування, глобальних перевірок.

    Inner middleware:
        Виконується ПІСЛЯ маршрутизації, але ДО handler.
        Додає дані у data — handler отримує через параметри (DI).
        Використовуємо для: dependency injection.

ПОРЯДОК РЕЄСТРАЦІЇ РОУТЕРІВ:
    dp.include_router(commands.router)  ← специфічні команди — ПЕРШИМИ
    dp.include_router(chat.router)      ← catch-all текст — ОСТАННІМ

    Чому порядок важливий?
        aiogram перевіряє роутери у порядку реєстрації.
        Якщо chat.router (F.text) стояв би першим — він перехопив би /reset,
        /stats тощо до того, як commands.router міг би їх обробити.
"""
import logging
import redis.asyncio as aioredis

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from app.config import config
from app.handlers import commands, chat
from app.middlewares.inject import InjectMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.repositories.history_repo import HistoryRepository
from app.repositories.rate_limit_repo import RateLimitRepository

# Імпортуємо MODEL_POOL для відображення у лозі запуску
# (показує весь ланцюг fallback: gemini-2.5-flash → gemini-2.5-flash-lite → ...)
from app.services.ai_service import MODEL_POOL

# Logger для цього модуля (у логах відображатиметься "app.bot | INFO | ...")
logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """
    Налаштовує глобальний формат і рівень логування.

    logging.basicConfig() конфігурує кореневий Logger один раз.
    Всі logger = logging.getLogger(__name__) у будь-якому модулі
    автоматично успадковують цю конфігурацію.

    Рівні (від найтихішого до найгучнішого):
        CRITICAL → ERROR → WARNING → INFO → DEBUG

    При level=INFO: показуються INFO, WARNING, ERROR, CRITICAL.
    При level=DEBUG: показуються ВСІ рівні (максимальна деталізація).

    Формат: "2025-05-18 14:30:00 | INFO     | app.bot | Повідомлення"
    """
    logging.basicConfig(
        # getattr(logging, "INFO") → logging.INFO (числова константа 20)
        # Дозволяє задавати рівень рядком з .env: LOG_LEVEL=DEBUG
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),

        # %(levelname)-8s: рівень вирівняний до 8 символів
        # ("INFO    ", "WARNING ", "ERROR   ") — для читабельності в терміналі
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",

        # Формат дати/часу у %(asctime)s
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_redis() -> aioredis.Redis:
    """
    Створює асинхронний Redis клієнт.

    aioredis.Redis — обгортка над redis-py з підтримкою asyncio.
    Всі методи (.get, .set, .incr, .ping тощо) — корутини (await).

    decode_responses=True:
        Redis внутрішньо зберігає дані як байти (b"hello").
        З цим параметром клієнт автоматично декодує байти у рядки.
        Без нього: await redis.get("key") → b"value" (bytes)
        З ним:    await redis.get("key") → "value" (str)

    Важливо: ця функція лише КОНФІГУРУЄ клієнт, але НЕ підключається.
    Реальне TCP-з'єднання встановлюється при першій команді (.ping у main.py).
    """
    return aioredis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        decode_responses=True,
    )


def create_bot() -> Bot:
    """
    Створює aiogram Bot — HTTP-клієнт для Telegram Bot API.

    Bot = об'єкт, що:
      - зберігає токен і підписує кожен HTTP-запит до api.telegram.org
      - надає методи: send_message(), get_updates(), set_webhook() тощо
      - управляє aiohttp ClientSession (пул з'єднань)

    DefaultBotProperties(parse_mode=ParseMode.HTML):
        Встановлює HTML parse_mode за замовчуванням для ВСІХ відповідей.
        Це означає, що <b>текст</b>, <i>текст</i>, <code>код</code>
        рендеряться у Telegram без явного parse_mode у кожному answer().

        Альтернативи parse_mode:
            ParseMode.HTML     — HTML теги: <b>, <i>, <code>, <pre>
            ParseMode.MARKDOWN — Markdown V2: **bold**, _italic_, `code`
            None               — звичайний текст без форматування
    """
    return Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(redis_client: aioredis.Redis) -> Dispatcher:
    """
    Збирає Dispatcher — центральну систему маршрутизації подій aiogram.

    Dispatcher:
      1. Отримує кожен Update від Telegram
      2. Передає через middleware (перевірки, ін'єкція залежностей)
      3. Знаходить відповідний роутер і handler
      4. Викликає handler з підготовленими даними (data dict)

    Параметр redis_client передається глибоко:
      - HistoryRepository: зберігає розмови у Redis
      - RateLimitRepository: зберігає лічильники запитів
      - InjectMiddleware: передає redis у handlers для Circuit Breaker
    """

    # ── Репозиторії ──────────────────────────────────────────────────────
    # Репозиторій — клас, що інкапсулює логіку роботи зі сховищем даних.
    # Handler не знає "де" і "як" зберігати — він просто викликає методи.
    # Якщо завтра замінити Redis на PostgreSQL — handler не зміниться.

    # HistoryRepository: зберігає JSON-список {role, content} у Redis.
    # Ключ: "history:{user_id}", TTL: 24 год.
    history_repo = HistoryRepository(redis_client)

    # RateLimitRepository: атомарні лічильники запитів (INCR + EXPIRE).
    # Ключ: "rate:{user_id}"
    rate_repo = RateLimitRepository(redis_client)

    # ── Dispatcher ───────────────────────────────────────────────────────
    dp = Dispatcher()

    # ── Middleware (ПОРЯДОК МАЄ ЗНАЧЕННЯ!) ───────────────────────────────

    # OUTER middleware: перехоплює ВСІ updates до будь-якого роутера.
    # RateLimitMiddleware перевіряє ліміт запитів.
    # Якщо перевищено: відповідає "Забагато запитів!" і робить return.
    # Handler взагалі НЕ викликається — Update відкинуто.
    dp.message.outer_middleware(RateLimitMiddleware(rate_repo))

    # INNER middleware: виконується після маршрутизації, перед Handler.
    # InjectMiddleware додає у data:
    #   data["history_repo"] = history_repo  → handler отримує через параметр
    #   data["redis"] = redis_client          → для Circuit Breaker в ai_service
    dp.message.middleware(InjectMiddleware(history_repo, redis_client))

    # ── Роутери (ПОРЯДОК = ПРІОРИТЕТ!) ───────────────────────────────────

    # commands.router: /start, /help, /reset, /stats, /history
    # Реєструємо ПЕРШИМ — щоб команди не перехоплювались catch-all handler
    dp.include_router(commands.router)

    # chat.router: F.text (будь-який текст) → AI
    # Реєструємо ОСТАННІМ — catch-all для всього, що не є командою
    dp.include_router(chat.router)

    return dp


async def set_bot_commands(bot: Bot) -> None:
    """
    Реєструє команди бота у Telegram Menu (кнопка ☰).

    Після виклику у Telegram з'явиться список команд з описами.
    Користувач може клікнути на команду — вона автоматично надішлеться.

    Це чисто UI-функція: не впливає на логіку обробки команд.
    Навіть без set_my_commands() команди /start, /reset тощо працюватимуть.

    BotCommand(command="start", description="..."):
        command — без "/" (Telegram додасть сам у меню)
        description — короткий опис (показується під командою)
    """
    await bot.set_my_commands([
        BotCommand(command="start",   description="Почати розмову"),
        BotCommand(command="reset",   description="Скинути пам'ять"),
        BotCommand(command="stats",   description="Статистика"),
        BotCommand(command="history", description="Показати історію"),
        BotCommand(command="help",    description="Допомога"),
    ])


async def on_startup(bot: Bot) -> None:
    """
    Lifecycle-хук: викликається ОДИН РАЗ при запуску бота.

    Реєструється у main.py: dp.startup.register(on_startup)
    Виконується після підключення до Telegram, але до обробки Updates.

    " → ".join(MODEL_POOL):
        Формує рядок для лога: "gemini-2.5-flash → gemini-2.5-flash-lite → ..."
        Показує весь ланцюг fallback у лозі запуску.
    """
    # Встановлюємо команди у Telegram Menu
    await set_bot_commands(bot)

    # get_me() → запит до Telegram, повертає User-об'єкт бота
    me = await bot.get_me()
    logger.info(
        "AI-бот запущено: @%s | Gemini MODEL_POOL: %s",
        me.username,
        " → ".join(MODEL_POOL),  # "gemini-2.5-flash → gemini-2.5-flash-lite → ..."
    )


async def on_shutdown(bot: Bot) -> None:
    """
    Lifecycle-хук: викликається при зупинці бота (Ctrl+C або помилка).

    Реєструється у main.py: dp.shutdown.register(on_shutdown)

    bot.session.close():
        Закриває aiohttp ClientSession всередині Bot.
        Без цього aiohttp виводить попередження про незакриті з'єднання.
    """
    logger.info("AI-бот зупиняється...")
    await bot.session.close()
