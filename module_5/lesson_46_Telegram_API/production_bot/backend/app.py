"""
backend/app.py — FastAPI Application Factory (Фабрика застосунку).

АРХІТЕКТУРНА РОЛЬ:
    Цей файл — єдина точка збірки всього production-боту.
    Три фабричні функції будують систему крок за кроком:

        create_bot()        → налаштовує aiogram Bot (token, ParseMode)
        create_dispatcher() → реєструє middleware + handlers
        create_app()        → збирає FastAPI, tax lifespan, монтує роутери

    Потім одна змінна: `app = create_app()` — її запускає uvicorn.

ЧОМУ FastAPI + aiogram, а не лише aiogram?
    aiogram (long polling або webhook) обробляє лише Telegram Updates.
    Але production-боту потрібно більше:

    ┌─────────────────────────────────────────────────────────┐
    │  FastAPI                                                 │
    │  ├── /webhook/{SECRET}   ← Telegram (aiogram Dispatcher)│
    │  ├── /admin/auth/token   ← JWT авторизація              │
    │  ├── /admin/users        ← управління користувачами     │
    │  ├── /admin/analytics    ← статистика                   │
    │  ├── /health             ← Docker/Nginx health check     │
    │  └── /docs               ← Swagger UI (тільки DEBUG)    │
    └─────────────────────────────────────────────────────────┘

    Один uvicorn-процес обробляє всі ці endpoint-и одночасно
    завдяки asyncio Event Loop.

LIFESPAN (запуск/зупинка):
    @asynccontextmanager lifespan — сучасна заміна on_startup/on_shutdown.

    Startup (до `yield`):
        1. bot.set_webhook() — реєструємо URL у Telegram
        2. bot.get_me() — перевіряємо що токен валідний

    Shutdown (після `yield`, при Ctrl+C або SIGTERM):
        1. bot.delete_webhook() — Telegram перестає надсилати Updates
        2. bot.session.close() — закриваємо HTTP-з'єднання
        3. close_redis() — закриваємо Redis pool

ПОРЯДОК ІНІЦІАЛІЗАЦІЇ (критично!):
    setup_logging() → settings.validate() → create_bot() → create_dispatcher()
    Якщо validate() кидає ValueError — застосунок не стартує,
    замість того щоб стартувати з порожнім BOT_TOKEN.

DOCS_URL В PRODUCTION:
    docs_url="/docs" if settings.DEBUG else None
    У production Swagger відключений — зменшує attack surface.
    Атакуючий не бачить список ендпоінтів та їх схеми.
"""
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI

from backend.api.admin.auth import router as auth_router
from backend.api.admin.users import router as users_router
from backend.api.admin.analytics import router as analytics_router
from backend.api.webhook import setup_webhook_router
from backend.bot.handlers import start
from backend.bot.middlewares.block_check import BlockCheckMiddleware
from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.core.redis import close_redis

logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    """
    Фабрика Bot — створює aiogram Bot з налаштуваннями за замовчуванням.

    DefaultBotProperties(parse_mode=ParseMode.HTML):
        HTML обраний замість MarkdownV2 бо він надійніший:
        - MarkdownV2 вимагає escaping _*[]()~`>#+-=|{}.! у тексті
        - HTML escaping лише: & → &amp;  < → &lt;  > → &gt;
        - Динамічні дані (імена юзерів) вимагають escaping завжди

    DefaultBotProperties — встановлює parse_mode для ВСІХ повідомлень бота.
    Не потрібно передавати parse_mode у кожному message.answer().

    Повертає:
        Bot — об'єкт що використовується у Dispatcher і webhook handler.
    """
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    """
    Фабрика Dispatcher — реєструє middleware і handlers.

    ПОРЯДОК РЕЄСТРАЦІЇ (критично!):
        1. outer_middleware(BlockCheckMiddleware()) — ПЕРШИЙ в ланцюгу
        2. include_router(start.router) — обробники команд

    ЧОМУ BlockCheckMiddleware — outer?
        Outer middleware виконується ДО того як Dispatcher вибере router.
        Це означає: заблокований юзер відкидається ще до парсингу команди.

        Схема потоку:
        Telegram Update
            ↓
        BlockCheckMiddleware (outer) → якщо blocked → return (мовчки ігнор)
            ↓
        Dispatcher вибирає router
            ↓
        Handler виконується

    ROUTER PRIORITY:
        dp.include_router() викликається один раз.
        У production-боті один router (start.router).
        При додаванні нових handlers: специфічні фільтри ЗАВЖДИ першими.

    Повертає:
        Dispatcher — готовий до прийому Updates від Telegram.
    """
    dp = Dispatcher()
    # Outer middleware — перша лінія захисту, виконується для кожного Update
    dp.update.outer_middleware(BlockCheckMiddleware())
    # Handlers: /start, /subscribe та інші команди
    dp.include_router(start.router)
    return dp


def create_app() -> FastAPI:
    """
    Головна фабрика — збирає весь FastAPI застосунок.

    Послідовність кроків:
    1. setup_logging() — налаштовуємо логування ПЕРШИМ
       (щоб validate() та bot() теж логувалися правильно)
    2. settings.validate() — перевіряємо всі обов'язкові env vars
       (при помилці кидає ValueError → uvicorn не стартує)
    3. create_bot() → create_dispatcher() — будуємо Telegram-шар
    4. lifespan контекст-менеджер — реєструємо запуск/зупинку
    5. FastAPI(...) — створюємо застосунок
    6. Монтуємо роутери: webhook + admin + health

    LIFESPAN vs ON_STARTUP/ON_SHUTDOWN:
        Старий підхід (deprecated):
            @app.on_event("startup")
            async def startup(): ...

        Новий підхід (Python 3.10+):
            @asynccontextmanager
            async def lifespan(app):
                # startup
                yield
                # shutdown

        Перевага: startup і shutdown живуть в одному місці → легше читати.
        Гарантія: навіть при помилці в startup, shutdown code після yield виконується.

    Повертає:
        FastAPI — об'єкт, який запускає uvicorn:
        CMD: uvicorn backend.app:app --host 0.0.0.0 --port 8000
    """
    # Крок 1: логування (завжди першим)
    setup_logging()
    # Крок 2: перевірка env vars (впаде тут, не в рантаймі)
    settings.validate()

    # Крок 3: Telegram-шар
    bot = create_bot()
    dp = create_dispatcher()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # ── STARTUP ───────────────────────────────────────────────────────
        # Реєструємо webhook у Telegram API.
        # Telegram буде надсилати POST на WEBHOOK_URL для кожного Update.
        # drop_pending_updates=True — відкидаємо Updates що накопичились
        # поки бот був offline (уникаємо обробки старих повідомлень).
        await bot.set_webhook(
            url=settings.WEBHOOK_URL,
            secret_token=settings.WEBHOOK_SECRET,  # для перевірки X-Telegram-Bot-Api-Secret-Token
            drop_pending_updates=True,
        )
        # get_me() — перевіряємо що BOT_TOKEN валідний і бот доступний
        me = await bot.get_me()
        logger.info("Webhook встановлено: %s | bot: @%s", settings.WEBHOOK_URL, me.username)

        yield  # ← тут застосунок працює (приймає запити)

        # ── SHUTDOWN ──────────────────────────────────────────────────────
        # Порядок важливий: спочатку Telegram, потім ресурси
        await bot.delete_webhook()          # Telegram перестає надсилати Updates
        await bot.session.close()           # закриваємо HTTP-з'єднання aiohttp
        await close_redis()                 # повертаємо Redis-з'єднання у pool
        logger.info("Shutdown complete")

    # Крок 4: FastAPI застосунок
    app = FastAPI(
        title="Telegram Bot Platform",
        version="1.0.0",
        # Swagger тільки в DEBUG — в production відключено для безпеки
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url=None,  # ReDoc теж вимкнено (зменшуємо attack surface)
        lifespan=lifespan,
    )

    # Крок 5: монтуємо роутери
    # Webhook — приймає Telegram Updates (POST /webhook/{SECRET})
    webhook_router = setup_webhook_router(bot, dp)
    app.include_router(webhook_router)

    # Admin API — захищені JWT endpoints для управління ботом
    app.include_router(auth_router)      # POST /admin/auth/token
    app.include_router(users_router)     # GET/POST /admin/users/*
    app.include_router(analytics_router) # GET /admin/analytics/overview

    # Health check — для Docker HEALTHCHECK та Nginx upstream перевірки
    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "environment": settings.ENVIRONMENT}

    return app


# Точка входу для uvicorn: uvicorn backend.app:app
# create_app() викликається при імпорті модуля.
app = create_app()
