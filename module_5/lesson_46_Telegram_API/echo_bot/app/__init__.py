"""
app/ — Головний пакет Echo-бота.

Містить:
    bot.py       — фабрики Bot/Dispatcher, lifecycle-хуки
    config.py    — конфігурація через змінні середовища (.env)
    handlers/    — обробники Telegram Updates (commands + echo)
    keyboards/   — UI компоненти (ReplyKeyboardMarkup)
    services/    — бізнес-логіка (user tracking)

Точка входу: main.py (у корені проєкту)
"""
