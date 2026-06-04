"""
main.py — Точка входу AI-бота.

РОЛЬ У АРХІТЕКТУРІ:
    Це єдиний файл, який запускається безпосередньо:
        python main.py

    Він відповідає за:
      1. Ініціалізацію логування
      2. Валідацію конфігурації (є токен? є API ключ?)
      3. Підключення до Redis
      4. Створення Bot та Dispatcher
      5. Реєстрацію lifecycle-хуків (startup / shutdown)
      6. Запуск нескінченного циклу polling

ЯК ПРАЦЮЄ asyncio.run():
    asyncio.run(main())
    │
    └── Створює новий Event Loop
        │
        └── Запускає корутину main() як першу задачу
            │
            └── dp.start_polling(bot) — нескінченний цикл:
                    while True:
                        updates = await bot.get_updates()   ← HTTP до Telegram
                        for update in updates:
                            await dp.process_update(update) ← через middleware → handler

ЧОМУ "finally: await redis_client.aclose()":
    Якщо бот зупиняється (Ctrl+C або виняток), блок finally гарантує,
    що Redis-з'єднання буде закрито коректно.
    Без цього — відкриті з'єднання "засмічують" пул підключень.

ПОВНИЙ PIPELINE одного повідомлення:
    User → Telegram → getUpdates → dp.feed_update()
        → RateLimitMiddleware (outer) → перевірка ліміту
        → InjectMiddleware (inner) → додає history_repo + redis у data
        → Handler (chat.py або commands.py)
        → ai_service.ask() → Google Gemini API
        → message.answer() → Telegram → User
"""
import asyncio
import logging

# Імпортуємо фабрики з app/bot.py
# Фабрика = функція, яка створює і налаштовує об'єкт
from app.bot import (
    create_bot,         # створює aiogram.Bot з токеном
    create_dispatcher,  # створює Dispatcher з middleware і роутерами
    create_redis,       # створює aioredis.Redis клієнт
    on_startup,         # хук — викликається при старті бота
    on_shutdown,        # хук — викликається при зупинці бота
    setup_logging,      # налаштовує формат і рівень логів
)
from app.config import config  # singleton об'єкт конфігурації

# Logger для цього модуля
# __name__ = "main" — буде відображатись у логах: "main | INFO | ..."
logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Головна async-функція — оркеструє запуск всього бота.

    Порядок ініціалізації важливий:
      1. Логування — першим, щоб всі наступні кроки видно у логах
      2. Конфігурація — до Redis/Bot, щоб не витрачати ресурси при помилці
      3. Redis — до Dispatcher, бо Dispatcher потребує репозиторії
      4. Bot + Dispatcher — фінальне налаштування
      5. Polling — нескінченний цикл, блокує до Ctrl+C
    """

    # =========================================================
    # КРОК 1: ЛОГУВАННЯ
    # =========================================================
    # Налаштовуємо формат, рівень і обробники логів.
    # Після цього всі logger.info/warning/error виводитимуться у термінал.
    setup_logging()

    # =========================================================
    # КРОК 2: ВАЛІДАЦІЯ КОНФІГУРАЦІЇ
    # =========================================================
    # Перевіряємо, чи встановлені обов'язкові змінні середовища.
    # Якщо ні — викидаємо ValueError зі списком проблем і зупиняємось.
    # Краще впасти тут, ніж отримати cryptic-помилку глибше в коді.
    config.validate()

    # =========================================================
    # КРОК 3: ПІДКЛЮЧЕННЯ ДО REDIS
    # =========================================================
    # create_redis() повертає aioredis.Redis — асинхронний клієнт.
    # Сам по собі він ще НЕ підключений — лише налаштований.
    redis_client = create_redis()

    # Перевіряємо живе підключення через PING команду.
    # Redis відповідає "PONG" — якщо відповів, сервер доступний.
    # Якщо Redis недоступний — відразу падаємо з помилкою.
    try:
        await redis_client.ping()
        logger.info("Redis підключено: %s:%s", config.REDIS_HOST, config.REDIS_PORT)
    except Exception as e:
        logger.error("Redis недоступний: %s", e)
        raise  # Перекидаємо виняток — бот не може працювати без Redis

    # =========================================================
    # КРОК 4: СТВОРЕННЯ BOT І DISPATCHER
    # =========================================================
    # Bot — HTTP-клієнт для Telegram Bot API
    # (відправляє запити, отримує updates)
    bot = create_bot()

    # Dispatcher — центральна точка маршрутизації:
    # передає redis_client, щоб Dispatcher міг створити репозиторії
    # та налаштувати middleware
    dp = create_dispatcher(redis_client)

    # =========================================================
    # КРОК 5: LIFECYCLE ХУКИ
    # =========================================================
    # Реєструємо функції, які викличуться при старті і зупинці.
    # dp.startup.register() — виконається ОДИН РАЗ перед першим polling.
    # dp.shutdown.register() — виконається при Ctrl+C або помилці.
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # =========================================================
    # КРОК 6: ЗАПУСК POLLING
    # =========================================================
    # start_polling() — нескінченний цикл:
    #   while True:
    #       updates = await getUpdates(offset=last_update_id + 1, timeout=30)
    #       for update in updates:
    #           await dp.process_update(update)
    #
    # drop_pending_updates=True:
    #   При запуску ігноруємо всі повідомлення, що накопичились
    #   поки бот був вимкнений. Це запобігає "флуду" при рестарті.
    #
    # finally: aclose() гарантує закриття Redis при будь-якій зупинці.
    try:
        await dp.start_polling(bot, drop_pending_updates=True)
    finally:
        # aclose() — асинхронне закриття з'єднання з пулом Redis
        await redis_client.aclose()


# =========================================================
# ТОЧКА ВХОДУ
# =========================================================
# if __name__ == "__main__":
#   Цей блок виконується ТІЛЬКИ коли файл запускається напряму:
#       python main.py
#   Якщо main.py імпортується як модуль — блок НЕ виконується.
#
# asyncio.run(main()):
#   1. Створює новий Event Loop
#   2. Запускає корутину main() у цьому Loop
#   3. Блокує головний потік до завершення main()
#   4. Закриває Event Loop і прибирає ресурси
if __name__ == "__main__":
    asyncio.run(main())
