"""
app/handlers/commands.py — Обробники команд бота.

РОЛЬ У АРХІТЕКТУРІ:
    Цей файл містить handlers для всіх Telegram-команд:
        /start   — привітання, скидання контексту
        /help    — довідка по використанню
        /reset   — очистити историю розмови
        /stats   — поточна статистика
        /history — перегляд историї у вигляді тексту

ЯК HANDLER ОТРИМУЄ ЗАЛЕЖНОСТІ (Dependency Injection):
    Коли aiogram викликає async def cmd_start(message, history_repo):
        - message: Message — з Update (автоматично з aiogram)
        - history_repo: HistoryRepository — з data["history_repo"] (з InjectMiddleware)

    InjectMiddleware (app/middlewares/inject.py) додає залежності у data словник.
    aiogram автоматично "впорскує" їх у параметри handler за іменем.

    Це і є Dependency Injection:
        Handler декларує що йому потрібно (параметри).
        Middleware готує це (data dict).
        aiogram з'єднує їх (inject).
        Handler не знає нічого про Redis — лише про HistoryRepository.

ROUTING PRIORITY:
    commands.router реєструється ПЕРШИМ у Dispatcher (bot.py).
    Завдяки цьому /reset, /stats тощо обробляються тут,
    а не перехоплюються chat.router (F.text).
"""
import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.repositories.history_repo import HistoryRepository
from app.config import config

# Logger для цього модуля
# У логах буде: "app.handlers.commands | INFO | ..."
logger = logging.getLogger(__name__)

# Router — контейнер для групи handlers.
# name="commands" — для дебагінгу та трейсингу (видно у логах aiogram).
# Dispatcher реєструє роутер через dp.include_router(commands.router).
router = Router(name="commands")


# =========================================================
# /START
# =========================================================
# CommandStart() — спеціальний оптимізований фільтр для /start.
# Чому CommandStart(), а не Command("start")?
#   CommandStart() також обробляє deep links:
#   /start ref_123 — де ref_123 це payload (referral code тощо).
#   Command("start") — лише чистий /start без payload.
@router.message(CommandStart())
async def cmd_start(message: Message, history_repo: HistoryRepository) -> None:
    """
    Handler для /start.

    Дії:
        1. Логуємо нового/поверненого користувача
        2. Скидаємо стару історію (щоразу /start — чистий аркуш)
        3. Надсилаємо привітання з поточною моделлю і списком команд

    history_repo отримується через DI з InjectMiddleware.
    Щоразу при /start контекст скидається — це UX-рішення:
        Якщо бот відповів щось неправильно — /start починає нову розмову.
    """
    user = message.from_user  # User — об'єкт з id, username, first_name

    # Логуємо подію: хто запустив бота
    # %s — lazy formatting, рядок форматується лише якщо рівень логу активний
    logger.info("Новий користувач: id=%s username=%s", user.id, user.username)

    # Скидаємо стару историю розмови у Redis.
    # Навіть якщо це перший запуск — clear() безпечний (нічого не робить).
    await history_repo.clear(user.id)

    # Відповідаємо привітанням.
    # HTML parse mode активний глобально (DefaultBotProperties у bot.py).
    # <b>текст</b> — жирний, рендеруватиметься у Telegram.
    await message.answer(
        f"Привіт, <b>{user.first_name}</b>! 🤖\n\n"
        # config.GEMINI_MODEL показує назву моделі з .env (default: gemini-2.5-flash)
        f"Я AI-асистент на базі <b>{config.GEMINI_MODEL}</b>.\n"
        f"Просто напиши своє запитання.\n\n"
        f"<b>Команди:</b>\n"
        f"/reset — скинути контекст розмови\n"
        f"/stats — статистика\n"
        f"/help — допомога",
        parse_mode="HTML",
    )


# =========================================================
# /HELP
# =========================================================
# Command("help") — фільтр, що спрацьовує на точний текст "/help".
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    Handler для /help.

    Показує:
        - Як користуватися ботом
        - Розмір вікна пам'яті (HISTORY_MAX_MESSAGES)
        - Ліміт запитів (RATE_LIMIT_REQUESTS / RATE_LIMIT_WINDOW)
        - Список всіх команд

    Залежностей (history_repo тощо) не потребує — лише config.
    """
    await message.answer(
        "<b>Як користуватися:</b>\n\n"
        "Просто пиши будь-яке запитання — я відповім.\n"
        # config.HISTORY_MAX_MESSAGES показує ліміт пам'яті з .env (default: 20)
        "Я пам'ятаю контекст розмови (останні "
        f"{config.HISTORY_MAX_MESSAGES} повідомлень).\n\n"
        # Показуємо ліміт rate limiting з конфігурації
        f"<b>Ліміт:</b> {config.RATE_LIMIT_REQUESTS} запитів "
        f"за {config.RATE_LIMIT_WINDOW} секунд.\n\n"
        "<b>Команди:</b>\n"
        "/start — почати знову\n"
        "/reset — скинути пам'ять розмови\n"
        "/stats — поточна статистика\n"
        "/history — переглянути историю\n"
        "/help — ця довідка",
        parse_mode="HTML",
    )


# =========================================================
# /RESET
# =========================================================
@router.message(Command("reset"))
async def cmd_reset(message: Message, history_repo: HistoryRepository) -> None:
    """
    Handler для /reset — очищає историю розмови у Redis.

    history_repo.clear(user_id):
        Виконує Redis DEL "history:{user_id}".
        Після цього наступний запит до AI розпочне нову розмову
        без будь-якого контексту з попередньої.

    Коли корисно:
        - Бот "застряг" у контексті і відповідає невідповідно
        - Хочемо нову тему без зв'язку з попередньою
        - Тестування/налагодження бота
    """
    # Видаляємо ключ "history:{user_id}" з Redis
    await history_repo.clear(message.from_user.id)

    # Підтверджуємо дію користувачу
    await message.answer("🔄 Контекст розмови скинуто. Починаємо з чистого аркуша!")


# =========================================================
# /STATS
# =========================================================
@router.message(Command("stats"))
async def cmd_stats(message: Message, history_repo: HistoryRepository) -> None:
    """
    Handler для /stats — показує поточну статистику.

    history_repo.count(user_id):
        Повертає кількість повідомлень у поточній историї.
        (читає з Redis і рахує довжину JSON-масиву)

    Показує:
        - Скільки повідомлень у пам'яті (з максимуму)
        - Яка модель використовується
        - Ліміт запитів
    """
    user_id = message.from_user.id

    # Рахуємо повідомлення у Redis для цього користувача
    msg_count = await history_repo.count(user_id)

    await message.answer(
        f"<b>📊 Статистика</b>\n\n"
        # msg_count / HISTORY_MAX_MESSAGES — показуємо використання пам'яті
        f"Повідомлень у пам'яті: <b>{msg_count}</b> / {config.HISTORY_MAX_MESSAGES}\n"
        f"Модель: <b>{config.GEMINI_MODEL}</b>\n"
        f"Ліміт: <b>{config.RATE_LIMIT_REQUESTS}</b> запитів / "
        f"{config.RATE_LIMIT_WINDOW}с",
        parse_mode="HTML",
    )


# =========================================================
# /HISTORY
# =========================================================
@router.message(Command("history"))
async def cmd_history(
    message: Message,
    history_repo: HistoryRepository,
) -> None:
    """
    Handler для /history — відображає повну историю розмови.

    Показує пронумерований список повідомлень:
        1. 🧑 Ви:
           Привіт, як справи?

        2. 🤖 AI:
           Добре, дякую! Чим можу допомогти?

    Обмеження:
        - Кожне повідомлення обрізається до 300 символів (щоб не "розпухало")
        - Весь текст обрізається до 4000 символів (ліміт Telegram: 4096)
    """
    user_id = message.from_user.id

    # Отримуємо список {role, content} з Redis
    history = await history_repo.get(user_id)

    # Якщо история порожня — повідомляємо і виходимо
    if not history:
        await message.answer(
            "📭 Історія порожня.\n"
            "Напиши щось боту 🙂"
        )
        return

    # ── Форматування историї ──────────────────────────────────────────
    lines = []

    for idx, msg in enumerate(history, start=1):
        role = msg["role"]       # "user" або "assistant"
        content = msg["content"]  # текст повідомлення

        # Різні префікси для user та assistant
        if role == "user":
            prefix = "🧑 Ви"
        else:
            prefix = "🤖 AI"

        # Обрізаємо дуже довгі повідомлення до 300 символів
        # "..." наприкінці — показує що текст продовжується
        if len(content) > 300:
            content = content[:300] + "..."

        lines.append(
            f"{idx}. {prefix}:\n"
            f"{content}"
        )

    # Об'єднуємо всі повідомлення через подвійний перенос рядка
    history_text = "\n\n".join(lines)

    # Telegram має ліміт 4096 символів на повідомлення.
    # Обрізаємо до 4000 з запасом (HTML теги займають місце).
    if len(history_text) > 4000:
        history_text = history_text[:4000] + "\n\n..."

    await message.answer(
        "<b>🧠 Історія розмови</b>\n\n"
        f"{history_text}",
        parse_mode="HTML",
    )
