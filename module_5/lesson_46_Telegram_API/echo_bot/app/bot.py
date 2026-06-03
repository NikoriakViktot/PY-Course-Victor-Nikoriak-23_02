"""
app/bot.py — Фабрики для Bot, Dispatcher + lifecycle-хуки.

РОЛЬ У АРХІТЕКТУРІ:
    Цей файл — "складальний цех" бота.
    Він не містить бізнес-логіки — лише збирає компоненти разом.

    Патерн "Factory Function":
        Замість глобальних об'єктів — функції, що повертають налаштовані об'єкти.

        ❌ Глобальний об'єкт (погано):
            bot = Bot(token=config.BOT_TOKEN)   ← виконується при імпорті!
            Якщо config ще не завантажений — помилка.

        ✅ Фабрика (правильно):
            def create_bot() -> Bot:
                return Bot(token=config.BOT_TOKEN)
            bot = create_bot()  ← викликається явно у main.py

        Переваги: легко тестувати, явний порядок ініціалізації.

ПОРЯДОК РЕЄСТРАЦІЇ РОУТЕРІВ (КРИТИЧНО!):
    dp.include_router(start.router)  ← /start, /help, /about, кнопки — ПЕРШИМИ
    dp.include_router(echo.router)   ← F.text catch-all — ОСТАННІМ

    aiogram перевіряє роутери у порядку реєстрації.
    Перший роутер, handler якого підходить — виграє.

    Якби echo.router стояв першим:
        F.text → TRUE для "/start" (це ж теж текст!)
        echo_text() обробив би команду замість cmd_start()
        Команди ніколи не дійшли б до start.router.

LIFECYCLE ХУКИ:
    on_startup() — викликається ОДИН РАЗ до першого polling:
        Реєструємо команди у Telegram Menu (/start, /help, /about)
        Логуємо username і ID бота для підтвердження запуску

    on_shutdown() — викликається при Ctrl+C або помилці:
        Закриваємо aiohttp ClientSession (уникаємо memory leaks)
"""
import logging

# Bot — HTTP-клієнт Telegram Bot API
# Dispatcher — центральний маршрутизатор Update-ів
from aiogram import Bot, Dispatcher

# DefaultBotProperties — глобальні параметри для всіх повідомлень
from aiogram.client.default import DefaultBotProperties

# ParseMode — enum з варіантами: HTML, MARKDOWNV2, None
from aiogram.enums import ParseMode

# BotCommand — структура Telegram-команди (command + description)
from aiogram.types import BotCommand

# Конфігурація з .env (singleton)
from app.config import config

# Роутери з handlers:
#   start.router → /start, /help, /about + кнопки клавіатури
#   echo.router  → F.text, F.photo, F.sticker, catch-all
from app.handlers import start, echo

# Logger для цього модуля (у логах: "app.bot | INFO | ...")
logger = logging.getLogger(__name__)


# =========================================================
# LOGGING SETUP
# =========================================================
def setup_logging() -> None:
    """
    Глобальна конфігурація logging системи Python.

    logging.basicConfig() конфігурує кореневий Logger ОДИН РАЗ.
    Всі logger = logging.getLogger(__name__) у будь-якому модулі
    автоматично успадковують цю конфігурацію.

    Рівні логування (від тихого до гучного):
        CRITICAL → ERROR → WARNING → INFO → DEBUG

    При level=DEBUG: показуються ВСІ рівні — максимальна деталізація.
    При level=INFO: показуються INFO і вище — стандарт для production.

    Формат:
        "2025-05-18 14:30:00 | INFO     | app.bot | Бот запущено"
         ^дата/час            ^рівень    ^модуль   ^повідомлення

    %(levelname)-8s: рівень вирівняний до 8 символів
        "INFO    " vs "WARNING " — рівне форматування у терміналі.
    """
    logging.basicConfig(
        # getattr(logging, "DEBUG") → logging.DEBUG (числова константа 10)
        # Дозволяє задавати рівень рядком з .env: LOG_LEVEL=WARNING
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),

        # Формат кожного рядка у логах
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",

        # Формат дати та часу
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# =========================================================
# BOT FACTORY
# =========================================================
def create_bot() -> Bot:
    """
    Створює aiogram Bot — HTTP-клієнт для Telegram Bot API.

    Bot = об'єкт, що:
      - Зберігає токен і підписує кожен HTTP-запит до api.telegram.org
      - Надає методи: send_message(), send_photo(), get_updates() тощо
      - Управляє aiohttp ClientSession (пул HTTP-з'єднань)

    DefaultBotProperties(parse_mode=ParseMode.HTML):
        Встановлює HTML parse_mode для ВСІХ відповідей бота за замовчуванням.

        Це означає: <b>текст</b>, <i>текст</i>, <code>код</code>
        рендеряться у Telegram БЕЗ явного parse_mode у кожному answer().

        Альтернативи parse_mode:
            ParseMode.HTML       → <b>, <i>, <code>, <pre>
            ParseMode.MARKDOWNV2 → **bold**, _italic_, `code`  (суворий синтаксис)
            None                 → звичайний текст без форматування

        Чому HTML, а не MarkdownV2?
            MarkdownV2 вимагає екранування _*[]()~`>#+-.!
            HTML надійніший: лише < > & потребують екранування.
    """
    return Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


# =========================================================
# DISPATCHER FACTORY
# =========================================================
def create_dispatcher() -> Dispatcher:
    """
    Створює Dispatcher та реєструє роутери у правильному порядку.

    Dispatcher — центральна система маршрутизації aiogram:
      1. Отримує кожен Update від Telegram
      2. Визначає тип (Message, CallbackQuery тощо)
      3. Шукає відповідний router і handler (перший збіг виграє)
      4. Викликає handler з потрібними параметрами

    Порядок include_router КРИТИЧНИЙ:
        Роутери перевіряються у порядку реєстрації.
        start.router реєструємо ПЕРШИМ — щоб специфічні команди
        і точні F.text == "..." фільтри не перехоплювались
        загальним F.text з echo.router.
    """
    # Dispatcher — event bus для всіх Telegram Updates
    dp = Dispatcher()

    # ── Роутер 1: команди і кнопки ──────────────────────────────────
    # start.router обробляє:
    #   /start  (CommandStart filter)
    #   /help   (Command filter)
    #   /about  (Command filter)
    #   "ℹ️ Про бота"  (F.text == "...")
    #   "❓ Допомога"  (F.text == "...")
    #
    # Реєструємо ПЕРШИМ: специфічні фільтри мають пріоритет.
    dp.include_router(start.router)

    # ── Роутер 2: ехо (catch-all) ────────────────────────────────────
    # echo.router обробляє:
    #   F.text   → echo_text()   — повторює текст
    #   F.photo  → echo_photo()  — відповідає на фото
    #   F.sticker → echo_sticker() — відповідає на стікер
    #   @router.message() → echo_unknown() — все інше
    #
    # Реєструємо ОСТАННІМ: catch-all не повинен перехоплювати команди.
    dp.include_router(echo.router)

    return dp


# =========================================================
# TELEGRAM COMMANDS MENU
# =========================================================
async def set_bot_commands(bot: Bot) -> None:
    """
    Реєструє команди бота у Telegram Menu (кнопка ☰).

    Після виклику у Telegram з'явиться список команд.
    Користувач може клікнути на команду — вона відправиться автоматично.

    Це чисто UI-функція: команди /start, /help, /about працюватимуть
    навіть без set_my_commands() — реєстрація лише для зручності UI.

    BotCommand:
        command     — назва без "/" (Telegram додасть сам)
        description — короткий опис, що показується в меню
    """
    commands = [
        BotCommand(command="start", description="Запустити бота"),
        BotCommand(command="help",  description="Допомога"),
        BotCommand(command="about", description="Про бота"),
    ]

    # Надсилаємо список до Telegram API
    await bot.set_my_commands(commands)

    logger.info("Команди бота зареєстровано в Telegram")


# =========================================================
# STARTUP HOOK
# =========================================================
async def on_startup(bot: Bot) -> None:
    """
    Lifecycle-хук: викликається ОДИН РАЗ при запуску polling.

    Реєструється у main.py: dp.startup.register(on_startup)
    Виконується після підключення до Telegram, але ДО обробки Updates.

    Типові задачі у on_startup:
        - Реєстрація команд у Telegram Menu
        - Підключення до бази даних
        - Прогрів кешу
        - Перевірка готовності зовнішніх сервісів
        - Логування інформації про запуск

    get_me():
        Telegram API метод, що повертає інформацію про поточного бота.
        Корисно для верифікації: логуємо username, щоб підтвердити
        що токен відповідає потрібному боту.
    """
    # Реєструємо команди у Telegram Menu (/start, /help, /about)
    await set_bot_commands(bot)

    # Отримуємо інформацію про бота для логу запуску
    me = await bot.get_me()

    logger.info(
        "Бот запущено: @%s (id=%s)",
        me.username,
        me.id,
    )


# =========================================================
# SHUTDOWN HOOK
# =========================================================
async def on_shutdown(bot: Bot) -> None:
    """
    Lifecycle-хук: викликається при зупинці бота.

    Реєструється у main.py: dp.shutdown.register(on_shutdown)
    Виконується при Ctrl+C або некритичній помилці.

    bot.session.close():
        Закриває aiohttp ClientSession всередині Bot.
        aiohttp використовує пул HTTP-з'єднань до api.telegram.org.

        Без явного закриття при завершенні програми:
            - aiohttp виводить ResourceWarning: "Unclosed client session"
            - З'єднання залишаються у TIME_WAIT стані на рівні OS
            - При частих рестартах накопичується "сміття" у мережевому стеку

    Типові задачі у on_shutdown:
        - Закриття HTTP сесій
        - Закриття підключень до БД
        - Збереження стану
        - Скасування background tasks
    """
    logger.info("Бот зупиняється...")

    # Закриваємо aiohttp ClientSession — прибираємо мережеві ресурси
    await bot.session.close()
