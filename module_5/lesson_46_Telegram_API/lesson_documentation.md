# Урок 46 — Telegram Bot API: Архітектура Подійно-Орієнтованих Backend Систем

**Модуль:** 5 — APIs, Bots & Production Systems  
**Складність:** beginner → intermediate → advanced  
**Мова:** Українська

---

## Зміст

1. [Що таке Telegram Bot — Системна картина](#1-що-таке-telegram-bot--системна-картина)
2. [Доставка подій: Polling vs Webhook](#2-доставка-подій-polling-vs-webhook)
3. [Архітектура: від User до Handler](#3-архітектура-від-user-до-handler)
4. [Asyncio та Telegram Bot — Чому це невіддільно](#4-asyncio-та-telegram-bot--чому-це-невіддільно)
5. [Beginner: Перший бот](#5-beginner-перший-бот)
6. [Intermediate: Роутери, клавіатури та FSM](#6-intermediate-роутери-клавіатури-та-fsm)
7. [Advanced: Middleware, Webhook, Production](#7-advanced-middleware-webhook-production)
8. [Планування задач у часі](#8-планування-задач-у-часі)
9. [Що відбувається під капотом](#9-що-відбувається-під-капотом)
10. [Типові помилки та антипатерни](#10-типові-помилки-та-антипатерни)
11. [Production Best Practices](#11-production-best-practices)
12. [Зв'язок з попередніми уроками](#12-звязок-з-попередніми-уроками)

---

## 1. Що таке Telegram Bot — Системна картина

### Головна ідея

Telegram-бот — це **не програма всередині застосунку Telegram**. Це звичайний backend-сервер, який спілкується з серверами Telegram через стандартний HTTPS API. Telegram-сервери виступають **посередниками** між вашим кодом і мобільними клієнтами — вони беруть на себе шифрування (MTProto), керування з'єднаннями і мільйони одночасних клієнтів.

```
Користувач → Telegram Client → [MTProto] → Telegram Server
                                                    │
                                           HTTPS Bot API
                                                    │
                                        Ваш Python Server
```

### Де боти використовуються в production

| Сценарій | Масштаб | Технологія |
|----------|---------|------------|
| Клієнтська підтримка | тисячі запитів/день | aiogram + PostgreSQL |
| AI-асистент | сотні тисяч повідомлень | aiogram + OpenAI + Redis |
| E-commerce бот | оплати, замовлення | aiogram + FastAPI + Stripe |
| Нотифікатор (CI/CD, моніторинг) | мільйони повідомлень/день | aiogram + Celery + RabbitMQ |

### Архітектурна аналогія: Ресторанна кухня

Telegram Bot API — це шаблон, який ви зустрічатимете скрізь у backend-розробці.

| Ресторан | Telegram Bot |
|----------|-------------|
| Офіціант | Telegram API — приймає замовлення (Updates) |
| Квиток із замовленням | Об'єкт `Update` (JSON) |
| Шеф-кухар (диспетчер) | `Dispatcher` — розподіляє між цехами |
| Спеціалізація цехів | Фільтри (`Command("start")`, `F.photo`) |
| Кухар | `Handler` — виконує бізнес-логіку |
| Су-шеф | `Middleware` — перевірка перед/після обробки |

---

## 2. Доставка подій: Polling vs Webhook

### Long Polling

Бот сам **активно опитує** Telegram-сервер через метод `getUpdates`. Якщо подій немає — з'єднання залишається відкритим певний час (довге опитування), потім закривається, і бот робить новий запит.

```
[ Bot Backend ]                          [ Telegram Server ]
      |                                          |
      | ------- GET /getUpdates --------------> |
      | <------- 200 OK (Empty) --------------- |
      |                                          |
      | ------- GET /getUpdates --------------> |
      |                                          | (Користувач пише)
      | <------- 200 OK (New Event JSON) ------- |
      |                                          |
      | ------- GET /getUpdates --------------> |
```

**Переваги Polling:**
- ✅ Не потрібен публічний IP, домен або SSL
- ✅ Працює локально, на ноутбуці, за NAT
- ✅ Ідеально для розробки та тестування

**Недоліки Polling:**
- ❌ Складно масштабувати горизонтально (кілька екземплярів конфліктують)
- ❌ Невелика додаткова затримка доставки
- ❌ Витрачає з'єднання на idle-запити

### Webhook

Ролі змінюються: Telegram **сам надсилає** HTTP POST на ваш сервер щоразу, коли щось трапляється. Ви реєструєте URL один раз через `setWebhook`, і далі пасивно слухаєте.

```
[ Bot Backend ]                          [ Telegram Server ]
      |                                          |
      | ------- POST /setWebhook(url) -------> | (одноразово)
      | <------- 200 OK ----------------------- |
      |                                          |
      |                                          | (Користувач пише)
      | <------- POST /url (Event JSON) -------- |
      | ------- 200 OK -----------------------> |
```

**Переваги Webhook:**
- ✅ Миттєва доставка подій (мінімальна затримка)
- ✅ Ідеально масштабується горизонтально (Load Balancer перед N серверами)
- ✅ Менше idle-з'єднань, ощадніше використання ресурсів

**Недоліки Webhook:**
- ❌ Потрібен публічний IP, домен і SSL-сертифікат
- ❌ Складніше налагодження локально (потрібен ngrok або VPS)
- ❌ Більш складна початкова конфігурація

### Порівняльна таблиця

| Критерій | Polling | Webhook |
|----------|---------|---------|
| Напрямок запиту | Bot → Telegram | Telegram → Bot |
| Затримка | Мала | Мінімальна |
| Інфраструктура | Мінімальна | Домен + SSL + публічний IP |
| Масштабованість | Складна | Нативна (Load Balancer) |
| Де використовувати | Dev, малий/середній бот | Production, high-traffic |

**Правило вибору:** Починайте з polling. Переходьте на webhook коли бот виходить у production і трафік зростає.

---

## 3. Архітектура: від User до Handler

### Повний шлях Update

Коли користувач натискає «Відправити», за мілісекунди відбувається:

```
1. Користувач надсилає повідомлення
         │
2. Telegram Server генерує JSON-об'єкт Update
         │
3. Bot отримує Update (polling або webhook)
         │
4. Dispatcher (кореневий роутер) приймає Update
         │
    ┌────▼─────────────────────────────────────┐
    │           OUTER MIDDLEWARES              │  ← перевірка бану, логування
    └────┬─────────────────────────────────────┘
         │
    ┌────▼─────────────────────────────────────┐
    │   Router 1: Filters → Handler 1A         │
    │   Router 2: Filters → Handler 2A, 2B     │  ← перший збіг виграє
    │   Router N: Filters → Handler NA         │
    └────┬─────────────────────────────────────┘
         │ перший фільтр повернув True
    ┌────▼─────────────────────────────────────┐
    │           INNER MIDDLEWARES              │  ← DB-сесія, i18n
    └────┬─────────────────────────────────────┘
         │
    ┌────▼─────────────────────────────────────┐
    │              HANDLER                     │  ← виконує бізнес-логіку
    └────┬─────────────────────────────────────┘
         │
5. Handler викликає Telegram API (sendMessage)
         │
6. Telegram доставляє відповідь користувачу
```

### Об'єкт Update

`Update` — це загальна обгортка над конкретними подіями:

```python
# Що може бути всередині Update
Update(
    update_id=123456,
    message=Message(...),             # Текстове повідомлення
    # АБО
    callback_query=CallbackQuery(...), # Натискання inline-кнопки
    # АБО
    chat_member=ChatMemberUpdated(...), # Зміна статусу учасника
    # АБО
    pre_checkout_query=...,            # Початок оплати
)
```

### Роутер: каскадна маршрутизація

Фільтри перевіряються **зверху вниз**. Перший збіг споживає подію — решта обробників не отримують її.

```python
# ❌ НЕБЕЗПЕЧНО: широкий фільтр стоїть першим
@router.message(F.text)         # Спіймає ВСЕ, включно з /help
async def catch_all(message): ...

@router.message(Command("help")) # НІКОЛИ не виконається!
async def help_cmd(message): ...
```

```python
# ✅ ПРАВИЛЬНО: специфічні фільтри — вище
@router.message(Command("help")) # Перевіряється першим
async def help_cmd(message): ...

@router.message(F.text)          # Спіймає все решту
async def catch_all(message): ...
```

---

## 4. Asyncio та Telegram Bot — Чому це невіддільно

### Проблема синхронного бота

Уявіть 1000 користувачів одночасно. Якщо код синхронний:

```
Користувач A: DB-запит 3 секунди...
                ← ВСІ 999 ЧЕКАЮТЬ ←
Користувач B: запит 0.1 секунди...
Користувач C: запит 0.5 секунди...
```

Десятий користувач у черзі чекає суму всіх попередніх запитів.

### Асинхронний Event Loop

```
Користувач A: await DB-запит → ПАУЗА (Event Loop вільний)
Користувач B: await answer() → ПАУЗА (Event Loop вільний)
Користувач C: await API-запит → ПАУЗА (Event Loop вільний)
...
[DB готова] → відновлюємо A → відповідь
[answer готова] → відновлюємо B → ...
```

### Ключова небезпека: blocking у async

```python
# ❌ КАТАСТРОФА: time.sleep блокує ВЕСЬ Event Loop
@router.message(Command("slow"))
async def bad_handler(message: Message):
    time.sleep(10)              # Всі 1000 користувачів чекають 10 секунд!
    await message.answer("Готово")

# ✅ ПРАВИЛЬНО: await asyncio.sleep звільняє Event Loop
@router.message(Command("slow"))
async def good_handler(message: Message):
    await asyncio.sleep(10)     # Тільки цей handler чекає; решта працюють
    await message.answer("Готово")
```

**Правило:** Якщо поряд з `aiogram` ви використовуєте бібліотеку для БД, HTTP або будь-якого I/O — вона **мусить** бути асинхронною. `requests` → `aiohttp`, `psycopg2` → `asyncpg`.

### Timeline 5 користувачів

```
T=0.0s  Користувач A: /slow → await asyncio.sleep(10) → SUSPENDED
T=0.1s  Користувач B: /fast → await answer("Швидко!") → відповідь → DONE
T=0.2s  Користувач C: /fast → відповідь → DONE
T=0.3s  Користувач D: /fast → відповідь → DONE
T=10.0s Користувач A: resume → answer("Готово!") → DONE
```
Всі отримали відповідь. `time.sleep(10)` замість `await asyncio.sleep(10)` — і кожен чекає по 10 секунд послідовно.

---

## 5. Beginner: Перший бот

### Встановлення

```bash
pip install aiogram
```

### Echo-бот — мінімальний приклад

```python
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message

# Токен отримуємо у @BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Bot — це HTTP-клієнт для Telegram API
# Dispatcher — кореневий роутер (він же перший Router)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Декоратор реєструє handler без будь-яких фільтрів
# Спіймає будь-яке повідомлення
@dp.message()
async def echo_handler(message: Message):
    # message.answer() — shortcut для sendMessage в той самий чат
    await message.answer(text=message.text)

async def main():
    # start_polling запускає нескінченний цикл getUpdates
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

### /start та /help команди

```python
from aiogram.filters import Command

@dp.message(Command("start"))
async def start_handler(message: Message):
    # message.from_user.first_name — ім'я користувача
    user_name = message.from_user.first_name
    await message.answer(
        f"Привіт, {user_name}! 👋\n"
        f"Я ехо-бот. Напиши що-небудь!"
    )

@dp.message(Command("help"))
async def help_handler(message: Message):
    help_text = (
        "Доступні команди:\n"
        "/start — привітання\n"
        "/help — ця довідка\n"
        "/echo — повторити текст"
    )
    await message.answer(help_text)
```

### Фільтрація за типом контенту

```python
from aiogram import F  # Magic Filter

@dp.message(F.text)    # Тільки текстові повідомлення
async def text_handler(message: Message):
    await message.answer(f"Ви написали: {message.text}")

@dp.message(F.photo)   # Тільки фото
async def photo_handler(message: Message):
    await message.answer("Отримав фото!")

@dp.message(F.sticker) # Тільки стікери
async def sticker_handler(message: Message):
    await message.answer(f"Стікер emoji: {message.sticker.emoji}")
```

### Що відбувається після `message.answer()`

`message.answer()` — це **не** `return`. Це HTTP POST до Telegram API. Функція **не завершується** після виклику.

```python
@router.message(Command("status"))
async def status_handler(message: Message):
    maintenance = True
    if maintenance:
        await message.answer("Технічні роботи.")
    # ❌ Немає return — виконання продовжується!
    await message.answer("Бот працює!")  # Відправиться ОБИДВА рази!
```

```python
# ✅ Правильно
async def status_handler(message: Message):
    if maintenance:
        await message.answer("Технічні роботи.")
        return  # Зупиняємо виконання
    await message.answer("Бот працює!")
```

---

## 6. Intermediate: Роутери, клавіатури та FSM

### Роутери — модульна архітектура

Замість одного файлу `bot.py` з сотнями handlers — окремі модулі за доменами:

```
bot/
├── main.py            ← точка входу, підключає роутери
├── handlers/
│   ├── start.py       ← /start, /help
│   ├── catalog.py     ← перегляд товарів
│   └── orders.py      ← FSM оформлення замовлення
└── keyboards/
    ├── reply.py        ← звичайні клавіатури
    └── inline.py       ← inline-клавіатури
```

```python
# handlers/start.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

# Кожен файл — свій Router
router = Router()

@router.message(Command("start"))
async def start(message: Message):
    await message.answer("Головне меню")
```

```python
# main.py
from aiogram import Bot, Dispatcher
from handlers import start, catalog, orders

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Підключаємо всі роутери до Dispatcher
dp.include_router(start.router)
dp.include_router(catalog.router)
dp.include_router(orders.router)
```

### Reply Keyboard

```python
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    # Кнопки з'являються замість стандартної клавіатури
    buttons = [
        [KeyboardButton(text="🛒 Каталог"), KeyboardButton(text="📦 Мої замовлення")],
        [KeyboardButton(text="📞 Підтримка")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@router.message(Command("start"))
async def start(message: Message):
    await message.answer("Головне меню:", reply_markup=get_main_keyboard())

@router.message(F.text == "🛒 Каталог")
async def catalog_handler(message: Message):
    await message.answer("Ось наш каталог...")
```

### Inline Keyboard та CallbackQuery

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

def get_product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="✅ Купити", callback_data=f"buy:{product_id}"),
            InlineKeyboardButton(text="ℹ️ Деталі", callback_data=f"info:{product_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("catalog"))
async def show_product(message: Message):
    await message.answer(
        "Товар #1 — Ноутбук\nЦіна: 25 000 грн",
        reply_markup=get_product_keyboard(product_id=1)
    )

@router.callback_query(F.data.startswith("buy:"))
async def buy_handler(callback: CallbackQuery):
    product_id = callback.data.split(":")[1]
    
    # ✅ ОБОВ'ЯЗКОВО: answer() закриває "годинник" на кнопці
    # Якщо не викликати — користувач бачить спінер нескінченно
    await callback.answer("Додано до кошика!")
    
    await callback.message.answer(f"Товар #{product_id} замовлено!")
```

### FSM — Finite State Machine

FSM — це інструмент для запам'ятовування **контексту діалогу**. Без FSM бот не знає, чому користувач раптово пише "Іван" або "25".

```
Без FSM:
  Бот: "Привіт! Як вас звати?"
  Юзер: "Іван"
  Бот: "???" (не розуміє, що це відповідь на питання)

З FSM:
  Бот: "Як вас звати?" → встановлює стан waiting_for_name
  Юзер: "Іван" → обробник бачить стан waiting_for_name, зберігає ім'я
  Бот: "Скільки вам років?" → встановлює стан waiting_for_age
  Юзер: "25" → обробник бачить стан waiting_for_age, завершує реєстрацію
```

```python
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# Визначаємо стани як клас
class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_age  = State()

@router.message(Command("register"))
async def start_registration(message: Message, state: FSMContext):
    await state.set_state(Registration.waiting_for_name)
    await message.answer("Введіть ваше ім'я:")

@router.message(Registration.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    # Зберігаємо ім'я у FSM-сховище
    await state.update_data(name=message.text)
    await state.set_state(Registration.waiting_for_age)
    await message.answer("Скільки вам років?")

@router.message(Registration.waiting_for_age)
async def get_age(message: Message, state: FSMContext):
    # Отримуємо всі збережені дані
    data = await state.get_data()
    name = data["name"]
    age = message.text
    
    await state.clear()  # Очищаємо стан після завершення
    await message.answer(f"Зареєстровано: {name}, {age} років!")
```

### MemoryStorage vs RedisStorage

```python
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

# MemoryStorage: дані у RAM — зникнуть при перезапуску!
dp = Dispatcher(storage=MemoryStorage())

# RedisStorage: дані персистентні — виживають перезапуск
storage = RedisStorage.from_url("redis://localhost:6379")
dp = Dispatcher(storage=storage)
```

**Питання для рефлексії:** Що станеться з реєстрацією користувача (FSM у MemoryStorage), якщо ви перезапустите бота для оновлення коду?
> Всі незавершені FSM-сесії зникнуть — дані у RAM. Рішення: `RedisStorage` або PostgreSQL-based storage для production.

---

## 7. Advanced: Middleware, Webhook, Production

### Middleware — "цибулина" навколо Handler

Middleware — це прошарки, які огортають обробники. Вони можуть:
- Перехоплювати будь-який Update до/після Handler
- Модифікувати `data` — словник, що передається в Handler
- Блокувати Update повністю (напр., заблоковані користувачі)

```
                    Update
                      │
         ┌────────────▼────────────┐
         │    Outer Middleware     │  ← спочатку тут
         │  ┌──────────────────┐  │
         │  │  Inner Middleware │  │  ← потім тут
         │  │  ┌────────────┐  │  │
         │  │  │  Handler   │  │  │  ← нарешті тут
         │  │  └────────────┘  │  │
         │  └──────────────────┘  │
         └─────────────────────────┘
                      │
                  Response
```

```python
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # До Handler: відкриваємо DB-сесію, додаємо в data
        async with self.db_pool.acquire() as connection:
            data["db"] = connection
            result = await handler(event, data)  # Виклик Handler
        # Після Handler: з'єднання автоматично повертається у пул
        return result

class BanMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = data["event_from_user"].id
        if user_id in BANNED_USERS:
            return  # Блокуємо Update — Handler не викликається
        return await handler(event, data)
```

```python
# Підключення middleware
dp.message.middleware(DatabaseMiddleware(db_pool))
dp.update.outer_middleware(BanMiddleware())
```

### Handler тепер отримує DB з data

```python
@router.message(Command("profile"))
async def profile(message: Message, db):  # db прийшов від middleware
    user = await db.fetchrow(
        "SELECT * FROM users WHERE telegram_id = $1",
        message.from_user.id
    )
    await message.answer(f"Ваш профіль: {user['name']}")
```

### Webhook + FastAPI — Production архітектура

```python
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update
import uvicorn

app = FastAPI()
bot = Bot(token=TOKEN)
dp = Dispatcher()

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL  = "https://your-domain.com" + WEBHOOK_PATH

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()

@app.post(WEBHOOK_PATH)
async def webhook_handler(request: Request):
    # Отримуємо JSON від Telegram, передаємо в Dispatcher
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Глобальний обробник помилок

```python
from aiogram.types import ErrorEvent
import logging

logger = logging.getLogger(__name__)

@dp.error()
async def error_handler(event: ErrorEvent):
    # Логуємо помилку — НЕ відправляємо собі в Telegram!
    # (ризик досягти ліміту Telegram API і заблокувати себе)
    logger.error(
        "Exception while handling update %s: %s",
        event.update.update_id,
        event.exception,
        exc_info=True
    )
```

---

## 8. Планування задач у часі

### Короткі async-затримки

```python
@router.message(Command("timer"))
async def timer_handler(message: Message):
    await message.answer("Таймер запущено на 10 секунд...")
    await asyncio.sleep(10)           # Тільки цей handler чекає
    await message.answer("⏰ Час вийшов!")
```

### Фоновий нагадувач (Background Task)

```python
import asyncio
from datetime import datetime, timedelta

# Простий нагадувач — фоновий цикл
tasks_storage: dict[int, dict] = {}  # user_id → task_info

async def reminder_loop(bot: Bot):
    while True:
        now = datetime.now()
        for user_id, task in list(tasks_storage.items()):
            # 15 хвилин до дедлайну
            if now >= task["deadline"] - timedelta(minutes=15):
                await bot.send_message(user_id, f"⚠️ 15 хвилин до: {task['title']}")
                del tasks_storage[user_id]
        await asyncio.sleep(60)  # Перевіряємо кожну хвилину

async def main():
    # Запускаємо фоновий цикл як окремий Task
    asyncio.create_task(reminder_loop(bot))
    await dp.start_polling(bot)
```

### APScheduler — production-рівень

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Kyiv"))

async def daily_report(bot: Bot):
    # Відправляємо щоденний звіт
    await bot.send_message(ADMIN_CHAT_ID, "📊 Щоденний звіт...")

async def main():
    # Виконувати щодня о 09:00 Київського часу
    scheduler.add_job(daily_report, "cron", hour=9, minute=0, args=[bot])
    scheduler.start()
    await dp.start_polling(bot)
```

### Важливо: Персистентність vs Volatile пам'ять

```
RAM (asyncio.sleep, dict tasks_storage):
  Перезапуск бота → всі задачі зникають!
  
PostgreSQL / Redis:
  Перезапуск бота → перевантажуємо задачі з БД
  Рішення для production!
```

```python
# При старті: відновлюємо задачі з БД
async def on_startup():
    pending_tasks = await db.fetch(
        "SELECT * FROM reminders WHERE scheduled_at > NOW()"
    )
    for task in pending_tasks:
        scheduler.add_job(
            send_reminder,
            "date",
            run_date=task["scheduled_at"],
            args=[bot, task["user_id"], task["message"]]
        )
```

---

## 9. Що відбувається під капотом

### HTTP-рівень: що насправді надсилається

Кожен `await message.answer("Hello")` — це HTTP POST:

```http
POST https://api.telegram.org/bot<TOKEN>/sendMessage
Content-Type: application/json

{
    "chat_id": 123456789,
    "text": "Hello",
    "parse_mode": "HTML"
}
```

Відповідь Telegram:
```json
{
    "ok": true,
    "result": {
        "message_id": 42,
        "from": {...},
        "chat": {...},
        "date": 1700000000,
        "text": "Hello"
    }
}
```

### Long Polling під капотом

```
Bot → GET /getUpdates?offset=0&timeout=30&limit=100
          │
          │ (Telegram тримає з'єднання відкритим до 30 секунд)
          │
          │ [Нова подія або timeout]
          │
Telegram → 200 OK { "updates": [...] }
          │
Bot → оновлює offset = last_update_id + 1
Bot → GET /getUpdates?offset=<новий>&timeout=30
          │
          └─ цикл повторюється нескінченно
```

### Event Loop + aiohttp під капотом

```
asyncio.run(dp.start_polling(bot))
              │
         Event Loop старт
              │
         ┌────▼─────────────────────────┐
         │  while True:                 │
         │    update = await getUpdates │ ← aiohttp: один HTTP-запит
         │    for upd in updates:       │
         │        create_task(          │
         │            dp.process(upd)   │ ← паралельна обробка
         │        )                     │
         └──────────────────────────────┘
```

`aiohttp` відкриває одне TCP-з'єднання і тримає його через `keep-alive`. Кожен `await` у handler — це `yield` назад до Event Loop, який одночасно обробляє інші Updates.

### Webhook flow під капотом

```
Telegram Server:
  Новий Update → знайти webhook URL для бота → HTTP POST → ваш сервер

Ваш FastAPI сервер:
  POST /webhook → uvicorn → ASGI → FastAPI → handler
                                              │
                                    dp.feed_update(update)
                                              │
                                    Dispatcher обробляє → Handler виконується
                                              │
                                    return {"ok": True} → Telegram отримує 200
```

Telegram чекає 200 OK протягом **60 секунд**. Якщо таймаут — повторює доставку. Тому handler має бути швидким; важку роботу — в background task або Celery.

---

## 10. Типові помилки та антипатерни

### ❌ Антипатерн 1: Blocking у async handler

```python
# НЕБЕЗПЕЧНО: блокує весь Event Loop
async def bad_handler(message: Message):
    import requests
    data = requests.get("https://api.example.com/data").json()  # Блокує!
    time.sleep(5)                                                # Блокує!
    result = heavy_computation()                                 # Блокує CPU!

# ✅ ПРАВИЛЬНО
async def good_handler(message: Message):
    async with aiohttp.ClientSession() as s:
        async with s.get("https://api.example.com/data") as r:
            data = await r.json()
    await asyncio.sleep(5)
    result = await loop.run_in_executor(executor, heavy_computation)
```

### ❌ Антипатерн 2: Глобальний словник замість FSM

```python
# НЕБЕЗПЕЧНО: race condition між користувачами
user_data = {}  # Спільна пам'ять!

async def set_name(message: Message):
    user_data["name"] = message.text  # User A і User B перезаписують один одного!
    await asyncio.sleep(2)
    await message.answer(f"Ваше ім'я: {user_data['name']}")  # Отримає ім'я User B!

# ✅ ПРАВИЛЬНО: FSMContext ізолює дані кожного користувача
async def set_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await asyncio.sleep(2)
    data = await state.get_data()
    await message.answer(f"Ваше ім'я: {data['name']}")
```

### ❌ Антипатерн 3: Широкий фільтр першим

```python
# НЕБЕЗПЕЧНО: /help ніколи не спрацює
@router.message(F.text)          # Спіймає /help як текст
async def catch_all(message): ...

@router.message(Command("help")) # Мертвий код
async def help_cmd(message): ...
```

### ❌ Антипатерн 4: Не закрита callback.answer()

```python
# НЕБЕЗПЕЧНО: користувач бачить спінер на кнопці вічно
@router.callback_query(F.data == "buy")
async def buy(callback: CallbackQuery):
    await process_payment()  # Якщо впаде exception — answer() не буде викликано

# ✅ ПРАВИЛЬНО
async def buy(callback: CallbackQuery):
    await callback.answer()  # Одразу закриваємо спінер
    await process_payment()  # Тепер помилка не заблокує UI
```

### ❌ Антипатерн 5: Логування помилок у Telegram

```python
# НЕБЕЗПЕЧНО: досягнемо rate limit і заблокуємо власний чат
@dp.error()
async def error_handler(event: ErrorEvent):
    await bot.send_message(ADMIN_ID, str(event.exception))  # Flood!

# ✅ ПРАВИЛЬНО: логуємо у файл або Sentry
@dp.error()
async def error_handler(event: ErrorEvent):
    logger.error("Error: %s", event.exception, exc_info=True)
    # Або: sentry_sdk.capture_exception(event.exception)
```

### ❌ Антипатерн 6: MemoryStorage у production

```python
# НЕБЕЗПЕЧНО: перезапуск бота = втрата всіх FSM-сесій
dp = Dispatcher(storage=MemoryStorage())

# ✅ ПРАВИЛЬНО для production
from aiogram.fsm.storage.redis import RedisStorage
storage = RedisStorage.from_url("redis://redis:6379/0")
dp = Dispatcher(storage=storage)
```

### ❌ Антипатерн 7: Токен у коді

```python
# НЕБЕЗПЕЧНО: токен потрапить у git history!
BOT_TOKEN = "1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw"

# ✅ ПРАВИЛЬНО
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
# .env файл → docker-compose.yml → secrets manager
```

---

## 11. Production Best Practices

### Структура проєкту

```
telegram_bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              ← точка входу
│   ├── config.py            ← pydantic Settings (env vars)
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py
│   │   ├── catalog.py
│   │   └── orders.py
│   ├── keyboards/
│   │   ├── reply.py
│   │   └── inline.py
│   ├── middlewares/
│   │   ├── database.py
│   │   └── throttling.py
│   ├── services/            ← бізнес-логіка поза handlers
│   │   ├── user_service.py
│   │   └── order_service.py
│   └── models/              ← SQLAlchemy або asyncpg моделі
├── .env                     ← секрети (не в git!)
├── .env.example             ← шаблон (в git)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### Конфігурація через pydantic Settings

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    bot_token: str
    database_url: str
    redis_url: str = "redis://localhost:6379"
    webhook_url: str | None = None
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Rate Limiting Middleware

```python
from aiogram.types import Message
from collections import defaultdict
import time

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self._last_call: dict[int, float] = defaultdict(float)
    
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user:
            now = time.time()
            last = self._last_call[user.id]
            if now - last < self.rate_limit:
                # Занадто часто — ігноруємо
                return
            self._last_call[user.id] = now
        return await handler(event, data)
```

### Logging

```python
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log"),
    ]
)

# Структурований лог для production (structlog)
import structlog
logger = structlog.get_logger()

async def order_handler(message: Message):
    logger.info("order_received", user_id=message.from_user.id, chat=message.chat.id)
```

### Docker Compose для production

```yaml
# docker-compose.yml
services:
  bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/botdb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: botdb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

### Retry та стійкість до помилок

```python
import asyncio
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError

async def safe_send(bot: Bot, chat_id: int, text: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            await bot.send_message(chat_id, text)
            return
        except TelegramRetryAfter as e:
            # Telegram просить зачекати (rate limit)
            await asyncio.sleep(e.retry_after)
        except TelegramForbiddenError:
            # Користувач заблокував бота — видаляємо з БД
            await db.execute("DELETE FROM users WHERE chat_id = $1", chat_id)
            return
        except Exception:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

---

## 12. Зв'язок з попередніми уроками

| Урок | Тема | Відношення до Telegram Bot |
|------|------|-----------------------------|
| 31 | HTTP Requests | Telegram Bot API — це HTTP; `aiohttp` замість `requests` |
| 32 | Threading | Telegram bot використовує cooperative multitasking, не потоки |
| 34 | Asyncio | Event Loop, `await`, `create_task` — основа будь-якого бота |
| 46 | **Telegram Bot API** | **Цей урок — синтез усього** |
| — | FastAPI | Webhook-архітектура будується на FastAPI + uvicorn |
| — | Redis/Celery | FSM storage, background tasks, масштабування |
