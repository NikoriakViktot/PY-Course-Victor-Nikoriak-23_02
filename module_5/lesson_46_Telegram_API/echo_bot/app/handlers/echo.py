
# """
# app/handlers/echo.py — Echo handlers з production-style observability.
#
# РОЛЬ У АРХІТЕКТУРІ:
#     Цей файл — "серце" ехо-бота. Обробляє весь вхідний контент:
#         F.text    → echo_text()    — повторює текстові повідомлення
#         F.photo   → echo_photo()   — відповідає на фото
#         F.sticker → echo_sticker() — відповідає на стікери
#         (catch-all) → echo_unknown() — все інше (документи, голос тощо)
#
# OBSERVABILITY LAYER (production-style):
#     Кожен handler ДЕТАЛЬНО логує вхідне і вихідне повідомлення.
#
#     Рівні логів, які тут використовуються:
#         INFO  → нормальні події (отримали текст, надіслали відповідь)
#         DEBUG → повний JSON дамп (детальна відлагодження)
#         WARNING → неочікуваний тип контенту (catch-all спрацював)
#
#     Дві helper-функції:
#         log_message_metadata() → INFO: основні поля (user, chat, content_type)
#         log_full_message()     → DEBUG: повний JSON через model_dump()
#
#     Для перегляду DEBUG логів — у .env встановити: LOG_LEVEL=DEBUG
#     Для production (без JSON дампів): LOG_LEVEL=INFO
#
# ЯК AIOGRAM СЕРІАЛІЗУЄ MESSAGE У JSON:
#     aiogram моделі — це Pydantic моделі.
#     message.model_dump(mode="json"):
#         Конвертує Pydantic об'єкт у Python dict (JSON serializable).
#         mode="json" → всі типи конвертуються у JSON-сумісні (datetime → str тощо).
#     json.dumps(..., indent=4, ensure_ascii=False):
#         Серіалізує dict у відформатований JSON рядок для логу.
#         ensure_ascii=False → кирилиця і емоджі зберігаються як є (не \uXXXX).
#
# ROUTING PRIORITY:
#     echo.router реєструється ДРУГИМ у Dispatcher (після start.router).
#     F.text — загальний фільтр (будь-який текст).
#     Завдяки порядку, /start /help /about та кнопки вже оброблені start.router
#     і до echo.router не доходять.
#
#     Порядок handlers У САМОМУ echo.router:
#         1. F.text    → специфічний текст
#         2. F.photo   → специфічне фото
#         3. F.sticker → специфічний стікер
#         4. catch-all → все інше (без фільтрів)
#     Catch-all ОСТАННІМ — щоб не перехоплювати text/photo/sticker.
#
# """
import json
import logging
from pprint import pformat

from aiogram import Router, F
from aiogram.types import Message

# Logger для цього модуля
# У логах: "app.handlers.echo | INFO | ..."
logger = logging.getLogger(__name__)

# Router — контейнер handlers.
# name="echo" видно у логах aiogram при дебагінгу маршрутизації.
router = Router(name="echo")


# =========================================================
# HELPER: ЛОГУВАННЯ МЕТАДАТИ
# =========================================================
def log_message_metadata(message: Message) -> None:
    """
    Логує основну метадату повідомлення на рівні INFO.

    Показує найважливіші поля без повного JSON.
    Підходить для production логування де повний JSON зайвий.

    Поля що логуються:
        message_id   — унікальний ID у чаті
        chat_id      — ID чату (= user_id у private)
        chat_type    — "private", "group", "supergroup", "channel"
        user_id      — Telegram user ID
        username     — @username (може бути None)
        first_name   — ім'я у Telegram
        content_type — ContentType enum: TEXT, PHOTO, STICKER тощо
        date         — datetime UTC коли надіслано

    from_user може бути None:
        Для системних повідомлень (channel post, pinned тощо) from_user = None.
        Використовуємо: message.from_user.id if message.from_user else None
        щоб не отримати AttributeError.

    """
    logger.info(
        "\n"
        "================ MESSAGE =================\n"
        "message_id:   %s\n"
        "chat_id:      %s\n"
        "chat_type:    %s\n"
        "user_id:      %s\n"
        "username:     %s\n"
        "first_name:   %s\n"
        "content_type: %s\n"
        "date:         %s\n"
        "==========================================",
        message.message_id,
        message.chat.id,
        message.chat.type,
        message.from_user.id if message.from_user else None,
        message.from_user.username if message.from_user else None,
        message.from_user.first_name if message.from_user else None,
        message.content_type,
        message.date,
    )


# =========================================================
# HELPER: ПОВНИЙ JSON ДАМ
# =========================================================
def log_full_message(message: Message) -> None:
    """
    Логує ПОВНИЙ JSON Telegram message на рівні DEBUG.

    model_dump(mode="json"):
        Pydantic/aiogram метод для конвертації моделі у словник.
        mode="json" — всі типи Python конвертуються у JSON-сумісні:
            datetime → ISO 8601 рядок ("2025-05-18T14:30:00")
            Enum → значення (ContentType.TEXT → "text")
            None → null
        Результат: вкладений Python dict (JSON-serializable).

    json.dumps(indent=4):
        Серіалізує dict у красиво відформатований JSON рядок:
            {
                "message_id": 123,
                "from": {
                    "id": 987,
                    "username": "user"
                }
            }

    ensure_ascii=False:
        Зберігає Unicode символи як є.
        False: "Привіт 🎉" (читабельно)
        True:  "Привіт \U0001f389" (нечитабельно)

    try/except:
        Серіалізація може впасти якщо є нестандартні поля.
        Не хочемо, щоб помилка логування вплинула на обробку повідомлення.

    """
    try:
        # Конвертуємо aiogram Pydantic модель у dict
        message_dict = message.model_dump(mode="json")

        logger.debug(
            "\n"
            "=================================================\n"
            "FULL TELEGRAM MESSAGE JSON\n"
            "=================================================\n"
            "%s\n"
            "=================================================",
            json.dumps(
                message_dict,
                indent=4,
                ensure_ascii=False,
            ),
        )

    except Exception as e:
        # Якщо серіалізація не вдалась — логуємо помилку, але не падаємо
        logger.exception("Не вдалося залогувати FULL JSON: %s", e)


# =========================================================
# TEXT HANDLER
# =========================================================
# F.text — фільтр aiogram:
#   TRUE  → message.text is not None (є текстове повідомлення)
#   FALSE → фото, стікер, документ тощо
#
# Спрацьовує на БУДЬ-ЯКИЙ текст, якщо start.router вже не обробив.
# (start.router стоїть першим у Dispatcher і перехоплює /start, /help тощо)
@router.message(F.text)
async def echo_text(message: Message) -> None:
    """
    Ехо handler для текстових повідомлень.

    Повний цикл з observability:
        1. log_message_metadata() → INFO лог основних полів
        2. log_full_message()     → DEBUG лог повного JSON
        3. Логуємо текст запиту
        4. Формуємо відповідь: "🔁 {оригінальний текст}"
        5. Логуємо намір відправити відповідь
        6. await message.answer() → відправляємо відповідь
        7. Логуємо повний JSON відповіді від Telegram

    message.answer() vs bot.send_message():
        message.answer(text) ← shortcut, автоматично chat_id=message.chat.id
        bot.send_message(chat_id=message.chat.id, text=text) ← повна форма
        Обидва еквівалентні, answer() зручніший у handlers.

    sent_message:
        await message.answer() повертає Message об'єкт (відправлене повідомлення).
        Telegram підтверджує доставку і повертає деталі:
            message_id  — ID нового повідомлення у чаті
            date        — UTC timestamp відправки
            тощо
        Логуємо для повної трасовності (incoming → outgoing).
    """
    # ── Observability: логуємо вхідне повідомлення ──────────────────
    log_message_metadata(message)
    log_full_message(message)

    # Логуємо бізнес-подію: отримали текстове повідомлення
    logger.info(
        "TEXT MESSAGE RECEIVED | user_id=%s | text=%s",
        message.from_user.id,
        message.text,
    )

    # ── Бізнес-логіка: ехо ──────────────────────────────────────────
    # Префікс 🔁 показує що це відображення, а не нова відповідь
    response_text = f"🔁 {message.text}"

    # ── Observability: логуємо намір відповісти ─────────────────────
    logger.info(
        "SENDING RESPONSE | chat_id=%s | response=%s",
        message.chat.id,
        response_text,
    )

    # ── Відправка відповіді ──────────────────────────────────────────
    # await — не блокуємо Event Loop під час HTTP-запиту до Telegram API
    # Повертає Message об'єкт з деталями відправленого повідомлення
    sent_message = await message.answer(response_text)

    # ── Observability: логуємо JSON відповіді від Telegram ──────────
    # Показує що саме Telegram "бачив" у відправленому повідомленні
    logger.debug(
        "\n"
        "================ OUTGOING MESSAGE ================\n"
        "%s\n"
        "==================================================",
        json.dumps(
            sent_message.model_dump(mode="json"),
            indent=4,
            ensure_ascii=False,
        ),
    )


# =========================================================
# PHOTO HANDLER
# =========================================================
# F.photo — фільтр aiogram:
#   TRUE → message.photo is not None (є фото)
#   FALSE → текст, стікер, документ тощо
#
# message.photo — це LIST PhotoSize об'єктів.
# Telegram надсилає одне фото у КІЛЬКОХ розмірах (thumbnail, mid, full).
# Список відсортований від найменшого до найбільшого.
# message.photo[-1] — найбільший варіант (оригінальний розмір).
@router.message(F.photo)
async def echo_photo(message: Message) -> None:
    """
    Handler для фотографій.

    Telegram Photo:
        Кожне фото = список PhotoSize об'єктів.
        PhotoSize: file_id, file_unique_id, width, height, file_size.
        Бот може завантажити фото через bot.download(file_id) або get_file().

        Для ехо-бота просто підтверджуємо отримання.
        Повне ехо фото потребує: await bot.send_photo(chat_id, photo=message.photo[-1].file_id)

    pformat(message.photo):
        pformat() (pretty format) — форматує Python об'єкти для читання у логах.
        Показує список PhotoSize об'єктів з їх атрибутами.
    """
    # Логуємо metadata і повний JSON
    log_message_metadata(message)
    log_full_message(message)

    # Логуємо бізнес-подію: скільки варіантів розміру фото надіслано
    logger.info(
        "PHOTO RECEIVED | user_id=%s | photo_sizes=%s",
        message.from_user.id,
        len(message.photo),  # кількість варіантів розміру (зазвичай 3-4)
    )

    # DEBUG: детальна інформація про кожен PhotoSize (file_id, width, height)
    logger.debug(
        "PHOTO DETAILS:\n%s",
        pformat(message.photo),
    )

    # Відповідаємо — без ехо фото (для спрощення навчального прикладу)
    response = (
        "📸 Отримав фото!\n"
        "Але ехо фото поки не підтримую."
    )

    logger.info(
        "SENDING PHOTO RESPONSE | chat_id=%s",
        message.chat.id,
    )

    await message.answer(response)


# =========================================================
# STICKER HANDLER
# =========================================================
# F.sticker — фільтр aiogram:
#   TRUE → message.sticker is not None
#   FALSE → текст, фото тощо
#
# message.sticker — Sticker об'єкт з полями:
#   file_id      — унікальний ID файлу (для завантаження)
#   emoji        — емоджі, пов'язаний зі стікером (може бути None)
#   set_name     — назва стікерпаку (може бути None)
#   is_animated  — чи анімований (TGS format)
#   is_video     — чи відео-стікер (WEBM format)
@router.message(F.sticker)
async def echo_sticker(message: Message) -> None:
    """
    Handler для стікерів.

    message.sticker.emoji:
        Емоджі, пов'язаний зі стікером.
        Може бути None для деяких стікерів — використовуємо or "😊" як fallback.

    message.sticker.set_name:
        Назва стікерпаку.
        None якщо стікер окремий (не з паку).
    """
    # Логуємо metadata і повний JSON
    log_message_metadata(message)
    log_full_message(message)

    # Логуємо деталі стікера: емоджі і назву паку
    logger.info(
        "STICKER RECEIVED | user_id=%s | emoji=%s | set=%s",
        message.from_user.id,
        message.sticker.emoji,   # емоджі стікера (None якщо немає)
        message.sticker.set_name, # назва паку (None якщо окремий)
    )

    # DEBUG: повний JSON Sticker об'єкта
    logger.debug(
        "STICKER JSON:\n%s",
        json.dumps(
            message.sticker.model_dump(mode="json"),
            indent=4,
            ensure_ascii=False,
        ),
    )

    # Відповідаємо з емоджі стікера
    # message.sticker.emoji or "😊" → fallback якщо emoji = None
    response = (
        f"Класний стікер! "
        f"{message.sticker.emoji or '😊'}"
    )

    logger.info(
        "SENDING STICKER RESPONSE | chat_id=%s",
        message.chat.id,
    )

    await message.answer(response)


# =========================================================
# FALLBACK (CATCH-ALL) HANDLER
# =========================================================
# @router.message() БЕЗ ФІЛЬТРІВ — catch-all.
# Спрацьовує на ВСЕ, що не перехопили попередні handlers:
#   документи, голосові, відео, контакти, локації тощо.
#
# КРИТИЧНО: реєструється ОСТАННІМ у router,
# інакше перехопив би text/photo/sticker до їх handlers.
#
# Чому варто мати catch-all:
#   Без нього aiogram мовчки ігнорував би нерозпізнані типи.
#   Краще явно повідомити користувача, що контент не підтримується.
@router.message()
async def echo_unknown(message: Message) -> None:
    """
    Fallback handler — обробляє всі нерозпізнані типи контенту.

    message.content_type:
        ContentType enum: DOCUMENT, VOICE, VIDEO, VIDEO_NOTE,
        CONTACT, LOCATION, POLL, DICE тощо.

    WARNING рівень:
        Catch-all — це нештатна ситуація з точки зору бізнес-логіки.
        WARNING сигналізує: "хтось надіслав щось незаплановане".
        У production це може означати: потрібно додати новий handler.
    """
    # Логуємо metadata і повний JSON (для аналізу що саме прийшло)
    log_message_metadata(message)
    log_full_message(message)

    # WARNING: несподіваний тип контенту
    logger.warning(
        "UNKNOWN CONTENT TYPE | type=%s | user_id=%s",
        message.content_type,
        message.from_user.id if message.from_user else None,
    )

    # Повідомляємо користувача що цей тип не підтримується
    await message.answer(
        "Я поки не підтримую цей тип контенту."
    )


# =========================================================
# ЩО ВИДНО У ЛОГАХ (при LOG_LEVEL=DEBUG)
# =========================================================
#
# При надходженні текстового повідомлення "Привіт":
#
# INFO  | ================ MESSAGE =================
#         message_id:   42
#         chat_id:      987654321
#         chat_type:    private
#         user_id:      987654321
#         username:     johndoe
#         first_name:   John
#         content_type: ContentType.TEXT
#         date:         2025-05-18 14:30:00+00:00
#         ==========================================
#
# DEBUG | =================================================
#         FULL TELEGRAM MESSAGE JSON
#         =================================================
#         {
#             "message_id": 42,
#             "from": {
#                 "id": 987654321,
#                 "is_bot": false,
#                 "first_name": "John",
#                 "username": "johndoe"
#             },
#             "chat": {
#                 "id": 987654321,
#                 "type": "private"
#             },
#             "date": "2025-05-18T14:30:00+00:00",
#             "text": "Привіт"
#         }
#         =================================================
#
# INFO  | TEXT MESSAGE RECEIVED | user_id=987654321 | text=Привіт
#
# INFO  | SENDING RESPONSE | chat_id=987654321 | response=🔁 Привіт
#
# DEBUG | ================ OUTGOING MESSAGE ================
#         { "message_id": 43, "text": "🔁 Привіт", ... }
#         ==================================================
#
# =========================================================
