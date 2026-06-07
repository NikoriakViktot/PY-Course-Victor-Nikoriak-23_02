"""
app/handlers/start.py — Обробники команд і кнопок головного меню.

РОЛЬ У АРХІТЕКТУРІ:
    Цей файл містить handlers для команд і кнопок клавіатури:
        /start  → cmd_start()  — привітання + реєстрація нового user
        /help   → cmd_help()   — список команд
        /about  → cmd_about()  — інформація про бота
        "ℹ️ Про бота"    → btn_about() — натискання кнопки
        "❓ Допомога"    → btn_help()  — натискання кнопки

ЧОМУ ЦЕЙ РОУТЕР РЕЄСТРУЄТЬСЯ ПЕРШИМ:
    У bot.py:
        dp.include_router(start.router)  ← ПЕРШИЙ
        dp.include_router(echo.router)   ← другий

    echo.router має handler F.text — він спрацьовує на БУДЬ-ЯКИЙ текст.
    Якщо б echo.router стояв першим:
        Користувач пише "ℹ️ Про бота"
        echo.router: F.text → TRUE → echo_text() показав би кнопку
        start.router: так і не отримав би шанс обробити

    З правильним порядком:
        start.router: F.text == "ℹ️ Про бота" → TRUE → btn_about() ✓
        echo.router: до нього вже не доходить

ЯК КНОПКИ КЛАВІАТУРИ ПЕРЕДАЮТЬ ТЕКСТ:
    ReplyKeyboard кнопка НЕ генерує callback — вона надсилає ТЕКСТОВЕ повідомлення.
    Кнопка "ℹ️ Про бота" → Telegram відправляє message.text = "ℹ️ Про бота"
    Це звичайне повідомлення, неввідрізне від того якби user надрукував вручну.

    Handler: @router.message(F.text == "ℹ️ Про бота")
    F.text == "ℹ️ Про бота" — точне порівняння рядків (case-sensitive).

DEPENDENCY INJECTION (без явного DI):
    start.py не використовує InjectMiddleware (цього немає у echo_bot).
    Але user_service імпортується безпосередньо.
    У ai_bot той самий принцип реалізований через middleware.

ПОВТОРНЕ ВИКОРИСТАННЯ КОД:
    btn_about() викликає cmd_about() — без дублювання логіки.
    btn_help()  викликає cmd_help().
    Це DRY принцип (Don't Repeat Yourself).
"""
import logging

# Router — контейнер для групи handlers
# F — "magic filter" для виразів: F.text, F.photo, F.text == "..."
from aiogram import Router, F

# CommandStart — оптимізований фільтр для /start (підтримує deep links)
# Command — фільтр для інших команд (/help, /about)
from aiogram.filters import Command, CommandStart

# Message — Pydantic модель Telegram повідомлення
from aiogram.types import Message

# Функція, що повертає ReplyKeyboardMarkup з кнопками
from app.keyboards.reply import get_main_keyboard

# Сервіс для відстеження унікальних користувачів
from app.services.user_service import register_user, get_total_users

# Logger для цього модуля
logger = logging.getLogger(__name__)

# Router — контейнер handlers цього файлу.
# name="start" видно у логах aiogram при дебагінгу маршрутизації.
# Реєструється у bot.py: dp.include_router(start.router)
router = Router(name="start")


# =========================================================
# /START
# =========================================================
# CommandStart() — фільтр, що спрацьовує на:
#   /start            ← простий запуск
#   /start ref_abc    ← deep link (payload після /start)
#
# Чому CommandStart(), а не Command("start")?
#   Command("start") — лише чистий /start
#   CommandStart() — також /start з payload
#   Для навчального бота різниця несуттєва,
#   але CommandStart() — правильна практика.
@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    Handler для /start — вітає користувача і показує клавіатуру.

    Дії:
        1. Реєструємо/ідентифікуємо користувача (user_service)
        2. Для нових user — логуємо і рахуємо
        3. Надсилаємо привітальне повідомлення з клавіатурою

    message.from_user:
        User об'єкт з полями: id, username, first_name, last_name, language_code.
        Використовуємо first_name для персоналізованого привітання.
    """
    # message.from_user — Telegram User об'єкт
    user = message.from_user

    # Реєструємо користувача у in-memory множині
    # Повертає True якщо перший раз, False якщо вже відомий
    is_new = register_user(user.id, user.username)

    if is_new:
        # Для нових користувачів показуємо порядковий номер
        # get_total_users() рахує скільки унікальних user бачив бот
        total = get_total_users()
        logger.info(
            "Новий старт! user_id=%s, всього users=%d",
            user.id,
            total,
        )

    # Надсилаємо привітання з Reply-клавіатурою.
    # reply_markup=get_main_keyboard():
    #   Прикріплює клавіатуру [ℹ️ Про бота] [❓ Допомога] до повідомлення.
    #   Клавіатура залишатиметься видимою до явного прибирання.
    # parse_mode="HTML":
    #   <b>текст</b> → жирний текст у Telegram.
    await message.answer(
        f"Привіт, <b>{user.first_name}</b>! 👋\n\n"
        f"Я ехо-бот — повторюю все, що ти пишеш.\n"
        f"Натисни /help щоб дізнатись більше.",
        reply_markup=get_main_keyboard(),
    )


# =========================================================
# /HELP
# =========================================================
# Command("help") — фільтр, що спрацьовує тільки на "/help".
# На відміну від CommandStart, Command() НЕ підтримує payload.
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    Handler для /help — показує довідку по командах.

    Не потребує залежностей (ні user_id, ні БД).
    Просто надсилає статичний текст з HTML форматуванням.

    <b>...</b> — жирний заголовок (HTML parse mode активний глобально).
    """
    await message.answer(
        "<b>Доступні команди:</b>\n\n"
        "/start — запустити бота\n"
        "/help — ця довідка\n"
        "/about — про бота\n\n"
        "Або просто напиши будь-який текст — я його повторю! 🔁",
        parse_mode="HTML",
    )


# =========================================================
# /ABOUT
# =========================================================
@router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    """
    Handler для /about — показує інформацію про бота і технологічний стек.

    <i>...</i> — курсив для підзаголовка (HTML parse mode).
    """
    await message.answer(
        "<b>Про бота</b>\n\n"
        "Навчальний ехо-бот для уроку 46.\n"
        "Стек: Python 3.12 + aiogram 3.x\n\n"
        "<i>Архітектура: Router → Handler → Response</i>",
        parse_mode="HTML",
    )


# =========================================================
# КНОПКИ REPLY KEYBOARD
# =========================================================
# ВАЖЛИВО — МЕХАНІЗМ РОБОТИ ReplyKeyboard:
#
#   ReplyKeyboardButton НЕ генерує callback events.
#   При натисканні вона просто надсилає ТЕКСТ як звичайне повідомлення.
#
#   Кнопка [ℹ️ Про бота] →  message.text = "ℹ️ Про бота"
#   Кнопка [❓ Допомога]  →  message.text = "❓ Допомога"
#
#   Фільтр F.text == "ℹ️ Про бота":
#       Точне порівняння рядків.
#       Спрацьовує ЛИШЕ якщо текст точно збігається (case-sensitive).
#
# ЧОМУ ЦІ HANDLERS У start.router, А НЕ У echo.router:
#   start.router реєструється ПЕРШИМ.
#   echo.router має F.text (catch-all) — якби кнопки були в echo.router,
#   F.text перехопив би натискання до перевірки F.text == "...".
#   Специфічні фільтри (== "точний текст") мають бути у роутері з вищим пріоритетом.


@router.message(F.text == "ℹ️ Про бота")
async def btn_about(message: Message) -> None:
    """
    Handler кнопки "ℹ️ Про бота" з Reply-клавіатури.

    Повторне використання: замість дублювання коду cmd_about()
    просто делегуємо до вже існуючої функції.

    await cmd_about(message):
        Передаємо той самий message об'єкт.
        cmd_about() нічого не знає про різницю між /about і кнопкою.
        Це DRY (Don't Repeat Yourself) принцип.
    """
    # Делегуємо до handler команди — не дублюємо код
    await cmd_about(message)


@router.message(F.text == "❓ Допомога")
async def btn_help(message: Message) -> None:
    """
    Handler кнопки "❓ Допомога" з Reply-клавіатури.

    Аналогічно btn_about() — делегуємо до cmd_help().
    Користувач може отримати довідку двома способами:
        1. Написати /help
        2. Натиснути кнопку [❓ Допомога]
    Обидва шляхи ведуть до одного результату.
    """
    # Делегуємо до handler команди
    await cmd_help(message)


# =========================================================
# МЕНТАЛНА МОДЕЛЬ: FLOW ПОДІЙ ДЛЯ КНОПКИ
# =========================================================
#
#   Користувач натиснув кнопку [ℹ️ Про бота]
#           ↓
#   Telegram надсилає Message з text="ℹ️ Про бота"
#           ↓
#   Dispatcher → start.router (першим у черзі)
#           ↓
#   Перевіряє фільтри:
#     CommandStart() → FALSE (не /start)
#     Command("help") → FALSE (не /help)
#     Command("about") → FALSE (не /about)
#     F.text == "ℹ️ Про бота" → TRUE ✓
#           ↓
#   Викликає btn_about(message)
#           ↓
#   btn_about() → await cmd_about(message)
#           ↓
#   Telegram отримує відповідь → User бачить текст
#
# =========================================================
