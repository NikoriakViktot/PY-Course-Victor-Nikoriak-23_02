"""
main.py — Точка входу Echo-бота.

РОЛЬ У АРХІТЕКТУРІ:
    Це єдиний файл, який запускається безпосередньо:
        python main.py

    Він відповідає за:
      1. Ініціалізацію логування (setup_logging)
      2. Валідацію конфігурації (є BOT_TOKEN?)
      3. Створення Bot та Dispatcher
      4. Реєстрацію lifecycle-хуків (startup/shutdown)
      5. Запуск нескінченного циклу Long Polling

ЩО ТАКЕ LONG POLLING:
    Бот сам звертається до Telegram кожні ~30 секунд:
        GET api.telegram.org/bot{TOKEN}/getUpdates?offset=N&timeout=30

    Telegram "тримає" з'єднання відкритим і відповідає одразу,
    щойно з'являється нове повідомлення (або після 30 сек таймауту).

    Альтернатива — Webhook: Telegram сам пушить updates до бота.
    Polling зручніший для розробки, webhook — для production.

ЯК ПРАЦЮЄ asyncio.run(main()):
    asyncio.run()
    │
    └── Створює новий Event Loop
        │
        └── Запускає корутину main()
            │
            └── dp.start_polling(bot) — нескінченний цикл:
                    while True:
                        updates = await bot.get_updates()   ← HTTP до Telegram
                        for update in updates:
                            await dp.process_update(update) ← через роутери → handler

ПОВНИЙ PIPELINE одного повідомлення від /start:
    User пише "/start" у Telegram
        → Telegram отримує → Servers
        → getUpdates() → Update JSON
        → dp.feed_update()
        → start.router → CommandStart() filter → cmd_start()
        → message.answer("Привіт!") → Telegram → User
"""
import asyncio
import logging

# Імпортуємо фабрики та lifecycle-хуки з app/bot.py
# Фабрика = функція, що створює і налаштовує об'єкт
from app.bot import (
    create_bot,        # створює aiogram.Bot з токеном
    create_dispatcher, # створює Dispatcher з роутерами
    on_startup,        # хук — викликається при старті бота
    on_shutdown,       # хук — викликається при зупинці
    setup_logging,     # налаштовує формат і рівень логів
)
from app.config import config  # singleton об'єкт конфігурації

# Logger для цього модуля
# __name__ = "main" — відображатиметься у логах: "main | INFO | ..."
logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Головна async-функція — оркеструє запуск бота.

    Порядок ініціалізації важливий:
      1. Логування — першим, щоб всі наступні кроки видно у логах
      2. Конфігурація — до Bot/Dispatcher, щоб не витрачати ресурси
      3. Bot + Dispatcher — налаштування об'єктів
      4. Хуки — реєстрація startup/shutdown callbacks
      5. Polling — нескінченний цикл, блокує до Ctrl+C
    """

    # =========================================================
    # КРОК 1: ЛОГУВАННЯ
    # =========================================================
    # Налаштовуємо формат і рівень логів для всього застосунку.
    # Після цього виклику всі logger.info/warning/error у будь-якому модулі
    # виводитимуться у термінал з однаковим форматом.
    setup_logging()

    # =========================================================
    # КРОК 2: ВАЛІДАЦІЯ КОНФІГУРАЦІЇ
    # =========================================================
    # Перевіряємо, чи встановлено BOT_TOKEN у .env.
    # Якщо ні — викидаємо ValueError з детальним поясненням що робити.
    # Краще явно впасти тут з зрозумілим повідомленням,
    # ніж отримати cryptic HTTP 401 Unauthorized набагато пізніше.
    config.validate()

    # =========================================================
    # КРОК 3: СТВОРЕННЯ BOT І DISPATCHER
    # =========================================================
    # Bot — HTTP-клієнт для Telegram Bot API
    bot = create_bot()

    # Dispatcher — центральна система маршрутизації:
    # приймає Updates і направляє до відповідних handlers
    dp = create_dispatcher()

    # =========================================================
    # КРОК 4: LIFECYCLE ХУКИ
    # =========================================================
    # dp.startup.register() — функція виконається ОДИН РАЗ до polling.
    # dp.shutdown.register() — функція виконається при Ctrl+C.
    # Хуки приймають Bot як параметр (aiogram передає автоматично).
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Запуск у режимі Long Polling...")

    # =========================================================
    # КРОК 5: ЗАПУСК LONG POLLING
    # =========================================================
    # start_polling() — нескінченний цикл:
    #   while True:
    #       updates = await getUpdates(offset=N, timeout=30)
    #       for update in updates:
    #           await dp.process_update(update)
    #
    # drop_pending_updates=True:
    #   Ігноруємо повідомлення, що накопичились поки бот був вимкнений.
    #   Корисно при розробці: не обробляємо "застарілі" тестові повідомлення.
    #   У production для фінансових/критичних ботів — False.
    await dp.start_polling(bot, drop_pending_updates=True)


# =========================================================
# ТОЧКА ВХОДУ ПРОГРАМИ
# =========================================================
# if __name__ == "__main__":
#   Виконується ТІЛЬКИ при прямому запуску: python main.py
#   Якщо main.py імпортується — блок НЕ виконується.
#   Це стандартна Python конвенція для "entry point" скриптів.
#
# asyncio.run(main()):
#   1. Створює новий Event Loop
#   2. Запускає корутину main() у цьому Loop
#   3. Блокує поточний потік до завершення (Ctrl+C)
#   4. Закриває Event Loop та прибирає ресурси (tasks, futures)
if __name__ == "__main__":
    asyncio.run(main())
