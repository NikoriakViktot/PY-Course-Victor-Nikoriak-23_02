# Урок 46 — Telegram Bot API: Ідеї для реалізації та бізнес-моделі

**Модуль:** 5 — APIs, Bots & Production Systems  
**Призначення:** Натхнення для pet-projects та production-рівня систем  
**Мова:** Українська

---

## Зміст

1. [Бізнес-моделі монетизації ботів](#1-бізнес-моделі-монетизації-ботів)
2. [Категорії ботів для реалізації](#2-категорії-ботів-для-реалізації)
3. [Боти з ШІ-інтеграцією](#3-боти-з-ші-інтеграцією)
4. [Медіа-боти](#4-медіа-боти)
5. [Inline-боти](#5-inline-боти)
6. [Боти для бізнесу та e-commerce](#6-боти-для-бізнесу-та-e-commerce)
7. [Боти для адміністрування спільнот](#7-боти-для-адміністрування-спільнот)
8. [Матриця складності та часу реалізації](#8-матриця-складності-та-часу-реалізації)

---

## 1. Бізнес-моделі монетизації ботів

### 1.1 Електронна комерція

Бот замінює повноцінний інтернет-магазин для малого та середнього бізнесу.

| Товар | Технологія оплати | БД | Складність |
|-------|------------------|-----|------------|
| Фізичні товари (одяг, техніка) | Telegram Payments + ЮКаса/Stripe | PostgreSQL | ⭐⭐⭐ |
| Цифрові товари (курси, арти) | Telegram Stars (обов'язково!) | SQLite / PostgreSQL | ⭐⭐ |
| Ігрові предмети / NFT | Telegram Stars | Redis + PostgreSQL | ⭐⭐⭐⭐ |

> **Правило Telegram:** Цифрові товари та послуги — **виключно Telegram Stars**. Фізичні товари можна продавати через зовнішні платіжні системи.

### 1.2 Платний контент та підписки

```
Рівні підписки (тарифи):
  Free     → базовий контент, обмежені запити до ШІ
  Basic    → 50 ШІ-запитів/день, ексклюзивний контент
  Premium  → безліміт, пріоритетна підтримка, ранній доступ
```

**Реалізація в БД:**

```python
# Таблиця підписок
CREATE TABLE subscriptions (
    user_id     BIGINT PRIMARY KEY,
    tier        VARCHAR(10),       -- 'free', 'basic', 'premium'
    expires_at  TIMESTAMP,
    stars_paid  INTEGER
);
```

### 1.3 Реклама та партнерки

| Модель | Дохід | Як реалізувати |
|--------|-------|----------------|
| Telegram Ads | **50% від доходу** Telegram ділиться з власником | Підключити монетизацію у @BotFather |
| Прямий продаж реклами | Фіксована ціна за пост | Бот відкладеного постингу + кнопки |
| Реферальна програма | % від транзакції реферала | `referrer_id` у таблиці users |

### 1.4 Сервісні боти для малого бізнесу

**Цифровий ресепшн** — замість сайту та адміністратора:

```
Перукарня / Салон краси:
  /start → Вибір майстра → Вибір послуги → Вибір дати/часу
         → Підтвердження → Запис у Google Calendar / БД
         → Нагадування за 24 год та 1 год до візиту

Ресторан:
  /book → Кількість осіб → Дата/час → Підтвердження
        → Бронювання → SMS/повідомлення адміністратору
```

### 1.5 Донати та пожертви

```python
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton

# Пресети для донатів (у Telegram Stars)
DONATION_PRESETS = [
    ("☕ Кава", 25),
    ("🍕 Піца", 50),
    ("💎 Меценат", 100),
]

async def donation_menu(message: Message):
    buttons = [
        [InlineKeyboardButton(
            text=f"{label} — {amount} ⭐",
            callback_data=f"donate:{amount}"
        )]
        for label, amount in DONATION_PRESETS
    ]
    # + кастомна сума
    buttons.append([InlineKeyboardButton(
        text="✏️ Своя сума",
        callback_data="donate:custom"
    )])
    await message.answer(
        "Підтримайте проєкт:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
```

---

## 2. Категорії ботів для реалізації

### За рівнем складності

```
⭐      Beginner  (1–3 дні)
⭐⭐    Intermediate (1–2 тижні)
⭐⭐⭐  Advanced (1–2 місяці)
⭐⭐⭐⭐ Production (команда + CI/CD)
```

---

## 3. Боти з ШІ-інтеграцією

### 3.1 Архітектурна пастка: async vs sync

```python
# ❌ НЕБЕЗПЕЧНО: стандартний OpenAI клієнт — синхронний!
from openai import OpenAI
client = OpenAI(api_key="...")

@router.message()
async def ai_handler(message: Message):
    # Блокує Event Loop для ВСІХ користувачів!
    response = client.chat.completions.create(...)

# ✅ ПРАВИЛЬНО: AsyncOpenAI
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key="...")

@router.message()
async def ai_handler(message: Message):
    # Event Loop вільний під час запиту до OpenAI
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": message.text}]
    )
    await message.answer(response.choices[0].message.content)
```

### 3.2 Ментальна модель: ШІ не знає контексту

Кожен запит до API нейромережі — чистий аркуш. Системний промт треба передавати **щоразу**:

```python
SYSTEM_PROMPT = """
Ти — корисний асистент, вбудований у Telegram-бот.
Відповідай українською мовою, коротко і по суті.
Не маєш доступу до попередньої історії чату.
"""

async def ask_ai(user_message: str) -> str:
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=500,
    )
    content = response.choices[0].message.content
    # ⚠️ Завжди перевіряємо на порожню відповідь
    if not content:
        return "ШІ не зміг сформувати відповідь. Спробуйте ще раз."
    return content
```

### 3.3 Ідеї ШІ-ботів

| Ідея | API | Складність | Монетизація |
|------|-----|------------|-------------|
| **Текстовий асистент** | OpenAI / OpenRouter | ⭐⭐ | Підписки за ліміти |
| **Аналіз фото з ШІ** | GPT-4o Vision | ⭐⭐⭐ | Stars за аналіз |
| **Генератор зображень** | DALL-E / Stable Diffusion | ⭐⭐⭐ | Stars за генерацію |
| **Розпізнавання мови** | Whisper API | ⭐⭐ | Stars за транскрипцію |
| **Переклад документів** | GPT-4o + PyPDF2 | ⭐⭐⭐ | Freemium |
| **ШІ-підтримка клієнтів** | OpenAI + knowledge base | ⭐⭐⭐⭐ | B2B SaaS |

### 3.4 Аналіз фото: повний хендлер

```python
import io
from PIL import Image
import base64

@router.message(F.photo)
async def analyze_photo(message: Message, bot: Bot):
    # 1. Показати "друкує..." поки обробляємо
    await bot.send_chat_action(message.chat.id, action="typing")
    
    # 2. Завантажити фото з Telegram (найбільший розмір = [-1])
    file_info = await bot.get_file(message.photo[-1].file_id)
    file_bytes = await bot.download_file(file_info.file_path)
    
    # 3. Кодуємо в base64 для передачі в OpenAI Vision
    img_b64 = base64.b64encode(file_bytes.read()).decode("utf-8")
    
    # 4. Асинхронний запит до GPT-4o Vision
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Детально опиши, що зображено на фото."},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}"
                }}
            ]
        }],
        max_tokens=300,
    )
    
    content = response.choices[0].message.content
    if not content:
        await message.answer("Не вдалося проаналізувати фото.")
        return
    
    await message.answer(content)
```

---

## 4. Медіа-боти

### 4.1 Обробка фотографій

| Ідея | Бібліотека | Складність |
|------|-----------|------------|
| Перетворення у малюнок олівцем | OpenCV | ⭐⭐ |
| Піксель-арт ефект | Pillow | ⭐ |
| Автокорекція яскравості (CLAHE) | OpenCV | ⭐⭐ |
| Генерація QR-кодів | `qrcode` | ⭐ |
| Водяний знак на фото | Pillow | ⭐ |
| Пошук облич на сайті | `requests` + OpenCV | ⭐⭐⭐ |
| Накладання тексту на зображення | Pillow + ImageDraw | ⭐ |

```python
import cv2
import numpy as np
from PIL import Image
import io

async def photo_to_pencil(photo_bytes: bytes) -> bytes:
    # Конвертуємо bytes → numpy array
    nparr = np.frombuffer(photo_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Алгоритм "олівець": сірий → інвертований → Gaussian blur → divide
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    inverted = 255 - gray
    blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
    pencil = cv2.divide(gray, 255 - blurred, scale=256.0)
    
    # Конвертуємо назад у bytes
    _, buffer = cv2.imencode(".jpg", pencil)
    return buffer.tobytes()

@router.message(F.photo)
async def pencil_effect(message: Message, bot: Bot):
    await bot.send_chat_action(message.chat.id, "upload_photo")
    file = await bot.get_file(message.photo[-1].file_id)
    photo_bytes = (await bot.download_file(file.file_path)).read()
    
    result = await asyncio.get_event_loop().run_in_executor(
        None, photo_to_pencil, photo_bytes  # CPU-bound → executor
    )
    await message.answer_photo(photo=BufferedInputFile(result, "pencil.jpg"))
```

### 4.2 Обробка відео

| Ідея | Бібліотека | Складність |
|------|-----------|------------|
| Обрізка відео | FFmpeg / MoviePy | ⭐⭐ |
| Конвертація AVI → MP4 | FFmpeg | ⭐ |
| Стиснення відео (CRF) | FFmpeg | ⭐⭐ |
| Склеювання відео | FFmpeg concat | ⭐⭐ |
| Відео → GIF | FFmpeg | ⭐ |
| Слайд-шоу з фото + MP3 | FFmpeg | ⭐⭐ |
| Хромакей (заміна фону) | Mediapipe + OpenCV | ⭐⭐⭐⭐ |
| Стабілізація відео | FFmpeg vidstab | ⭐⭐⭐ |
| Вимір швидкості авто | OpenCV + optical flow | ⭐⭐⭐⭐ |
| Заміна аудіодоріжки | FFmpeg | ⭐⭐ |

```python
import asyncio
import tempfile
import os

@router.message(F.video)
async def compress_video(message: Message, bot: Bot):
    await bot.send_chat_action(message.chat.id, "upload_video")
    
    # Завантажуємо відео у тимчасовий файл
    file = await bot.get_file(message.video.file_id)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_in:
        await bot.download_file(file.file_path, destination=tmp_in)
        input_path = tmp_in.name
    
    output_path = input_path.replace(".mp4", "_compressed.mp4")
    
    # FFmpeg: CRF=28 = гарна якість при меншому розмірі
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", input_path,
        "-vcodec", "libx264", "-crf", "28",
        output_path, "-y",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    
    await message.answer_video(video=FSInputFile(output_path))
    os.unlink(input_path)
    os.unlink(output_path)
```

### 4.3 Обробка аудіо

| Ідея | Бібліотека | Складність |
|------|-----------|------------|
| Відео → MP3 | FFmpeg | ⭐ |
| Обрізка аудіо | pydub / FFmpeg | ⭐ |
| Транскрипція голосу | Whisper API / faster-whisper | ⭐⭐ |
| Редагування метаданих MP3 | Mutagen | ⭐ |
| Злиття аудіо + відео | FFmpeg | ⭐ |

---

## 5. Inline-боти

Inline-бот викликається в **будь-якому чаті** через `@botname запит` — без додавання бота в групу.

```
Користувач в групі пише: @mybot кросівки nike
Telegram відкриває список результатів від бота
Користувач обирає → бот надсилає від імені користувача
```

### 5.1 Архітектура inline-обробника

```python
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import hashlib

@dp.inline_query()
async def inline_handler(query: InlineQuery):
    search_text = query.query.strip()
    
    # Шукаємо в БД або зовнішньому API
    results_data = await db.search_items(search_text, limit=10)
    
    results = []
    for item in results_data:
        results.append(
            InlineQueryResultArticle(
                id=hashlib.md5(str(item["id"]).encode()).hexdigest(),
                title=item["title"],
                description=item["description"],
                input_message_content=InputTextMessageContent(
                    message_text=f"**{item['title']}**\n{item['url']}",
                    parse_mode="Markdown"
                ),
                thumbnail_url=item.get("image_url"),
            )
        )
    
    # cache_time=300 → Telegram кешує результати 5 хвилин
    await query.answer(results, cache_time=300, is_personal=True)
```

### 5.2 Ідеї inline-ботів

| Ідея | Що шукає | Монетизація |
|------|---------|-------------|
| **Бот-сховище посилань** | власні збережені посилання | — |
| **Музичний бот** | треки + 10с семпл → повна пісня | Реклама |
| **Вікторина-бот** | готові опитування → надіслати в групу | — |
| **Курси валют** | актуальні курси НБУ / Binance | — |
| **Пошук рецептів** | рецепти за інгредієнтом | Affiliate |
| **Стікер-пак** | власні стікери → надіслати | Premium |
| **GIF-пошук** | Tenor / GIPHY API | Реклама |
| **Бот вакансій** | вакансії з БД або hh.ua | B2B |

---

## 6. Боти для бізнесу та e-commerce

### 6.1 Магазин з каталогом та кошиком (⭐⭐⭐)

```
Архітектура БД:
  users        → telegram_id, name, phone, referrer_id
  categories   → id, name, emoji
  products     → id, category_id, name, price, stock, photo_id
  cart_items   → user_id, product_id, quantity
  orders       → id, user_id, status, total, address, created_at
  order_items  → order_id, product_id, quantity, price_at_purchase
  subscriptions→ user_id, tier, expires_at
```

```python
# FSM для оформлення замовлення
class OrderFSM(StatesGroup):
    choosing_category = State()
    choosing_product  = State()
    viewing_cart      = State()
    entering_address  = State()
    confirming_order  = State()
    awaiting_payment  = State()
```

### 6.2 Реферальна система

```python
from aiogram.filters import CommandStart
from aiogram.types import Message
import re

@router.message(CommandStart(deep_link=True))
async def start_with_referral(message: Message, command: CommandObject, db):
    referral_code = command.args  # /start ref_123456789
    
    # Парсимо referrer_id
    if referral_code and referral_code.startswith("ref_"):
        referrer_id = int(referral_code.replace("ref_", ""))
        
        # Зберігаємо зв'язок
        await db.execute(
            "INSERT INTO users (telegram_id, referrer_id) VALUES ($1, $2) "
            "ON CONFLICT (telegram_id) DO NOTHING",
            message.from_user.id, referrer_id
        )
        
        # Нараховуємо бонус реферу (напр. 15%)
        await db.execute(
            "UPDATE users SET bonus_balance = bonus_balance + 15 WHERE telegram_id = $1",
            referrer_id
        )

# Генерація реферального посилання
async def get_referral_link(user_id: int, bot_username: str) -> str:
    return f"https://t.me/{bot_username}?start=ref_{user_id}"
```

### 6.3 Запис на послуги (⭐⭐⭐)

```python
class BookingFSM(StatesGroup):
    choosing_service  = State()
    choosing_master   = State()
    choosing_date     = State()
    choosing_time     = State()
    confirming        = State()
    entering_phone    = State()

# Клавіатура з вільними слотами
async def get_time_slots_keyboard(date: str, master_id: int, db) -> InlineKeyboardMarkup:
    booked = await db.fetch(
        "SELECT time_slot FROM bookings WHERE date=$1 AND master_id=$2",
        date, master_id
    )
    booked_times = {row["time_slot"] for row in booked}
    
    all_slots = ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"]
    buttons = []
    for slot in all_slots:
        if slot in booked_times:
            buttons.append([InlineKeyboardButton(text=f"❌ {slot}", callback_data="busy")])
        else:
            buttons.append([InlineKeyboardButton(
                text=f"✅ {slot}",
                callback_data=f"slot:{date}:{slot}"
            )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
```

---

## 7. Боти для адміністрування спільнот

### 7.1 Модераційні боти

| Бот | Функція | Реалізація |
|-----|---------|------------|
| **Join Hider** | Видалення системних повідомлень про вхід/вихід | `chat_member` handler |
| **WatchDog** | Видалення спаму і стоп-посилань | `F.text` + regex |
| **No Arabic** | Захист від арабського спаму | `re.search(r'[؀-ۿ]', text)` |
| **OrgRobot** | Капча для нових учасників | FSM + `ChatJoinRequest` |
| **Freq Robot** | Обмеження кількості повідомлень/день | Redis counter + TTL |
| **Grep Robot** | Видалення за стоп-словами | БД стоп-слів + фільтр |

```python
# Капча для нових учасників
from aiogram.types import ChatJoinRequest
import random

@dp.chat_join_request()
async def new_member_captcha(event: ChatJoinRequest, bot: Bot):
    # Генеруємо математичний приклад
    a, b = random.randint(1, 10), random.randint(1, 10)
    correct = a + b
    
    # Зберігаємо у Redis з TTL 60 секунд
    await redis.setex(f"captcha:{event.from_user.id}", 60, correct)
    
    # Відправляємо приватне повідомлення
    await bot.send_message(
        event.from_user.id,
        f"Для входу в групу розв'яжіть приклад:\n"
        f"**{a} + {b} = ?**",
        parse_mode="Markdown"
    )

@router.message(F.text.regexp(r'^\d+$'))
async def check_captcha(message: Message, bot: Bot):
    stored = await redis.get(f"captcha:{message.from_user.id}")
    if stored and int(message.text) == int(stored):
        # Схвалюємо запит
        await bot.approve_chat_join_request(CHAT_ID, message.from_user.id)
        await message.answer("✅ Вітаємо в групі!")
        await redis.delete(f"captcha:{message.from_user.id}")
    else:
        await message.answer("❌ Невірна відповідь. Спробуйте ще раз.")
```

### 7.2 Аналітичний бот для YouTube (⭐⭐⭐)

```python
from youtube_comment_downloader import YoutubeCommentDownloader
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io

@router.message(F.text.regexp(r'youtube\.com|youtu\.be'))
async def analyze_youtube(message: Message):
    await message.answer("⏳ Збираю коментарі...")
    
    downloader = YoutubeCommentDownloader()
    comments = []
    
    # Збираємо до 500 коментарів
    for comment in downloader.get_comments_from_url(message.text, sort_by=0):
        comments.append(comment["text"])
        if len(comments) >= 500:
            break
    
    # Генеруємо хмару тегів
    text = " ".join(comments)
    wordcloud = WordCloud(
        width=800, height=400,
        background_color="white",
        max_words=100
    ).generate(text)
    
    # Конвертуємо у bytes для Telegram
    buffer = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    
    await message.answer_photo(
        photo=BufferedInputFile(buffer.read(), "wordcloud.png"),
        caption=f"Хмара слів з {len(comments)} коментарів"
    )
```

---

## 8. Матриця складності та часу реалізації

| Проєкт | Складність | Час | Технологія | Монетизація |
|--------|-----------|-----|-----------|-------------|
| Echo-бот | ⭐ | 1 год | aiogram | — |
| Бот-довідник (FAQ) | ⭐ | 1 день | aiogram + SQLite | — |
| Бот нагадувань | ⭐⭐ | 3 дні | aiogram + APScheduler + Redis | — |
| Inline-пошук | ⭐⭐ | 3 дні | aiogram + зовнішній API | Реклама |
| ШІ-асистент | ⭐⭐ | 1 тиждень | aiogram + AsyncOpenAI | Підписки/Stars |
| Медіа-редактор (фото) | ⭐⭐ | 1 тиждень | aiogram + OpenCV/Pillow | Stars |
| Магазин (каталог+оплата) | ⭐⭐⭐ | 2–3 тижні | aiogram + PostgreSQL + Payments | Direct sales |
| Запис на послуги | ⭐⭐⭐ | 2 тижні | aiogram + PostgreSQL + Calendar API | B2B SaaS |
| Бот-модератор | ⭐⭐⭐ | 2 тижні | aiogram + Redis + PostgreSQL | Підписка |
| Медіа-редактор (відео) | ⭐⭐⭐ | 3 тижні | aiogram + FFmpeg + Celery | Stars |
| ШІ-підтримка клієнтів | ⭐⭐⭐⭐ | 1–2 місяці | aiogram + OpenAI + FastAPI + vector DB | B2B |
| Платформа ботів | ⭐⭐⭐⭐ | 3+ місяці | Мікросервіси + Kubernetes | Platform fee |

---

## Стек для production бота

```
Мінімальний (малий бот):
  aiogram 3.x + SQLite + APScheduler → 1 VPS

Середній (e-commerce, підписки):
  aiogram + PostgreSQL + Redis + Celery → Docker Compose на VPS

Великий (> 100k users):
  aiogram + FastAPI (webhook) + PostgreSQL Cluster
  + Redis Cluster + RabbitMQ + Celery
  + Nginx Load Balancer + Docker Swarm / Kubernetes
  + Sentry (моніторинг помилок) + Grafana (метрики)
```
