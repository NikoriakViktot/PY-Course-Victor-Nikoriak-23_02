"""
app/keyboards/ — Пакет UI-компонентів (клавіатур) бота.

Модулі:
    reply.py — ReplyKeyboardMarkup (кнопки внизу екрану)

Reply vs Inline клавіатури:
    Reply  — надсилає текст при натисканні → обробляється як message
    Inline — генерує callback_query → обробляється як callback

Handlers не конструюють кнопки самостійно — вони викликають
функції з цього пакету (наприклад get_main_keyboard()).
"""
