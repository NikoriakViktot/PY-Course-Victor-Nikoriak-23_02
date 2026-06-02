"""
app/keyboards/inline.py — Inline-клавіатури для повідомлень.

РОЛЬ У АРХІТЕКТУРІ:
    Inline-клавіатура — кнопки, що прикріпляються безпосередньо до повідомлення.
    На відміну від Reply-клавіатури (кнопки під полем введення),
    inline кнопки є частиною конкретного повідомлення.

INLINE vs REPLY КЛАВІАТУРА:
    Reply keyboard (ReplyKeyboardMarkup):
        - Кнопки з'являються замість клавіатури знизу екрану
        - Натискання надсилає ТЕКСТОВЕ повідомлення (message.text = "кнопка")
        - Зберігається між повідомленнями (поки не прибрати)
        - Простіший для базових команд (echo_bot)

    Inline keyboard (InlineKeyboardMarkup):
        - Кнопки прикріплені до конкретного повідомлення
        - Натискання генерує CallbackQuery (НЕ текстове повідомлення)
        - CallbackQuery містить callback_data (рядок до 64 байт)
        - Зникає разом з повідомленням
        - Підходить для: підтвердження, навігація, вибір опцій

ЯК ОБРОБЛЯТИ CALLBACK:
    Щоб кнопки "Скинути контекст" і "Статистика" спрацювали,
    потрібен окремий handler з фільтром F.data:

        @router.callback_query(F.data == "reset_history")
        async def on_reset(callback: CallbackQuery, history_repo: HistoryRepository):
            await history_repo.clear(callback.from_user.id)
            await callback.answer("✅ Скинуто")  # Прибирає "loading" spinner на кнопці
            await callback.message.edit_text("Контекст скинуто!")

    У поточній версії бота callback handlers не реалізовані —
    клавіатура підготовлена для майбутнього розширення.

СТРУКТУРА InlineKeyboardMarkup:
    InlineKeyboardMarkup(
        inline_keyboard=[         ← список рядів
            [кнопка1, кнопка2],   ← ряд 1 (горизонтально)
            [кнопка3],            ← ряд 2 (одна кнопка)
        ]
    )
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_reset_keyboard() -> InlineKeyboardMarkup:
    """
    Повертає inline-клавіатуру з двома кнопками.

    Кнопки розташовані горизонтально в одному ряду:
        [ 🔄 Скинути контекст ]  [ 📊 Статистика ]

    InlineKeyboardButton:
        text          — текст на кнопці (що бачить користувач)
        callback_data — рядок до 64 байт, який Telegram надішле боту при натисканні
                        у вигляді CallbackQuery (НЕ Message)

    callback_data "reset_history":
        При натисканні Telegram надішле CallbackQuery з data="reset_history".
        Handler може обробити це: @router.callback_query(F.data == "reset_history")

    callback_data "show_stats":
        Аналогічно для статистики.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                # Перша кнопка у ряду — скидання контексту
                InlineKeyboardButton(
                    text="🔄 Скинути контекст",
                    callback_data="reset_history",  # ідентифікатор для handler
                ),
                # Друга кнопка у тому самому ряду — статистика
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="show_stats",  # ідентифікатор для handler
                ),
            ]
            # Якщо потрібен другий ряд — додати сюди наступний список:
            # [InlineKeyboardButton(text="...", callback_data="...")]
        ]
    )
