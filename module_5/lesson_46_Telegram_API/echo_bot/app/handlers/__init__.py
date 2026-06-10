"""
app/handlers/ — Пакет обробників (handlers) Telegram Updates.

Роутери реєструються у bot.py у правильному порядку пріоритету:
    dp.include_router(start.router)  ← 1. команди + кнопки (специфічні)
    dp.include_router(echo.router)   ← 2. catch-all ехо (загальні)

Модулі:
    start.py — /start, /help, /about та кнопки Reply-клавіатури
    echo.py  — ехо тексту, фото, стікерів + fallback для решти

Правило: специфічні фільтри завжди реєструються перед загальними.
"""
