# AI Assistant Bot — Урок 46 (Intermediate ⭐⭐)

Telegram-бот з інтеграцією Google Gemini. Демонструє fault-tolerant AI gateway (MODEL_POOL + Circuit Breaker), Redis для стану та Middleware-архітектуру aiogram 3.

---

## Структура проєкту

```
ai_bot/
├── app/
│   ├── config/
│   │   └── settings.py         ← конфігурація через .env
│   ├── handlers/
│   │   ├── commands.py         ← /start /help /reset /stats
│   │   └── chat.py             ← головний AI handler (F.text)
│   ├── keyboards/
│   │   └── inline.py           ← inline-кнопки
│   ├── middlewares/
│   │   ├── rate_limit.py       ← обмеження частоти запитів (Redis)
│   │   └── inject.py           ← впорскування залежностей у handlers
│   ├── repositories/
│   │   ├── history_repo.py     ← зберігання историї розмов (Redis)
│   │   └── rate_limit_repo.py  ← лічильники rate limit (Redis)
│   ├── services/
│   │   └── ai_service.py       ← Gemini Gateway (MODEL_POOL + Circuit Breaker)
│   ├── utils/
│   │   └── text.py             ← хелпери (truncate, escape_html)
│   └── bot.py                  ← Bot, Dispatcher, middleware setup
├── main.py                     ← точка входу
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

---

## Чому Google Gemini, а не OpenAI?

| | OpenAI | Google Gemini |
|---|---|---|
| Безкоштовна квота | ❌ платна з першого запиту | ✅ Gemini 2.0 Flash: 15 req/min, 1M tokens/day |
| API ключ | кредитна картка обов'язкова | безкоштовно на [aistudio.google.com](https://aistudio.google.com) |
| SDK | `AsyncOpenAI` (natively async) | `google-genai` (sync → `asyncio.to_thread`) |
| Якість | GPT-4o | Gemini 2.5 Flash (порівнянна) |

Для навчального проєкту Gemini — очевидний вибір: **нульова вартість на старті**.

---

## Чому asyncio.to_thread, а не прямий await?

Google Gemini SDK (`google-genai`) — **синхронна** бібліотека. Прямий виклик заблокує Event Loop:

```python
# ❌ НЕПРАВИЛЬНО: sync виклик у async handler = заморозка всього бота
async def handle_message(message: Message):
    client = genai.Client(api_key=...)
    response = client.models.generate_content(...)  # ВЕСЬ бот завмирає на 3-10 сек!
    await message.answer(response.text)

# ✅ ПРАВИЛЬНО: запускаємо sync виклик у ThreadPool — Event Loop залишається вільним
async def handle_message(message: Message):
    text = await asyncio.to_thread(_call_gemini_sync, model, prompt, sys_prompt)
    await message.answer(text)
```

**При 10 одночасних users:**
- Прямий sync виклик: user #10 чекає ~60 сек (9 × ~6с кожен запит)
- `asyncio.to_thread`: всі 10 отримують відповідь паралельно (~6с)

---

## MODEL_POOL — каскадний fallback

Gemini Flash може повертати `503 Service Unavailable` у пікові години. Замість краша — автоматично пробуємо наступну модель:

```python
MODEL_POOL = [
    "gemini-2.5-flash",       # primary — найкраща якість
    "gemini-2.5-flash-lite",  # швидший fallback
    "gemini-2.0-flash",       # старше покоління, інша квота
    "gemini-2.0-flash-lite",  # найлегший, останній шанс
]
```

```
ask() → gemini-2.5-flash → 503 → gemini-2.5-flash-lite → ok ✓
                                        ↑ логується як attempt #2
```

\module_5\lesson_46_Telegram_API\ai_bot> docker compose up --build

---

## Circuit Breaker (Redis)

Якщо всі моделі падають (збій квоти, проблема з API) — Circuit Breaker зупиняє нові запити до Gemini на 5 хвилин, щоб не генерувати зайвий трафік:

```
5 невдалих спроб підряд → circuit OPEN (TTL 300s)
    ↓
Всі нові запити → "🔴 AI тимчасово недоступний"  (без виклику Gemini)
    ↓
Через 5 хвилин → circuit auto-CLOSE → нормальна робота
```

| Redis ключ | Значення | TTL |
|---|---|---|
| `ai_bot:cb:failures` | лічильник помилок (0–5) | 300 сек |
| `ai_bot:cb:open` | прапор "circuit open" (1) | 300 сек |

---

## Middleware Lifecycle

```
Message
  ↓
RateLimitMiddleware (outer)   ← перехоплює ВСІ updates до роутерів
  ↓ якщо ліміт перевищено
  drop + "Забагато запитів!"  ← handler взагалі не викликається
  ↓ якщо ok
InjectMiddleware (inner)      ← додає history_repo + redis у data handler
  ↓
Handler (chat.py)             ← отримує залежності через параметри
```

```python
# Outer — виконується до маршрутизації
dp.message.outer_middleware(RateLimitMiddleware(rate_repo))

# Inner — виконується безпосередньо перед handler
dp.message.middleware(InjectMiddleware(history_repo, redis_client))
```

---

## Налаштування

### 1. Отримати ключі

**Telegram Bot Token** — через [@BotFather](https://t.me/BotFather):
```
/newbot → назва → юзернейм → копіюємо токен
```

**Gemini API Key** — безкоштовно:
1. Відкрити [aistudio.google.com](https://aistudio.google.com)
2. `Get API Key` → `Create API key`
3. Скопіювати ключ (починається з `AIza...`)

### 2. Налаштувати .env

```bash
cp .env.example .env
```

Відредагувати `.env`:
```env
BOT_TOKEN=1234567890:AAF...your_token_here
GEMINI_API_KEY=AIzaSy...your_key_here
```

---

## Запуск локально

```bash
# 1. Redis (потрібен для историї + rate limit + circuit breaker)
docker run -d -p 6379:6379 --name redis redis:7-alpine

# 2. Залежності
pip install -r requirements.txt

# 3. Запуск
python main.py
```

## Запуск через Docker Compose

```bash
cp .env.example .env
# Заповнити BOT_TOKEN та GEMINI_API_KEY

docker compose up --build
```

---

## Команди бота

| Команда | Опис |
|---------|------|
| `/start` | Початок розмови, скидання контексту |
| `/help` | Допомога та список команд |
| `/reset` | Скинути пам'ять розмови |
| `/stats` | Кількість повідомлень у пам'яті |
| Текст | AI-відповідь з урахуванням контексту |

---

## Redis: що зберігається

| Ключ | Значення | TTL |
|------|----------|-----|
| `history:{user_id}` | JSON-список `[{role, content}]` | 24 год |
| `rate:{user_id}` | Лічильник запитів у вікні | `RATE_LIMIT_WINDOW` сек |
| `ai_bot:cb:failures` | Лічильник збоїв Gemini API | 5 хв |
| `ai_bot:cb:open` | Прапор "circuit open" | 5 хв |

---

## Архітектурні рішення

**Чому репозиторій, а не прямий Redis у handler:**  
Handler не знає деталей Redis (ключі, серіалізація, TTL). Репозиторій інкапсулює це. Якщо замінити Redis на PostgreSQL — handler не зміниться.

**Чому system prompt у кожному запиті:**  
Gemini API stateless — кожен запит незалежний. Системний контекст передаємо явно через `system_instruction` у `GenerateContentConfig`.

**Чому `asyncio.to_thread`, а не `async` метод SDK:**  
`google-genai` — синхронна бібліотека без async-варіанту. `to_thread` запускає її у ThreadPool, не блокуючи Event Loop aiogram.

**Чому `drop_pending_updates=True`:**  
При перезапуску бота ігноруємо накопичені повідомлення. Для систем де важлива кожна подія — `False` + persisted queue.

**Чому Circuit Breaker через Redis, а не в пам'яті:**  
In-memory стан втрачається при рестарті контейнера. Redis зберігає стан між рестартами і між кількома інстансами бота (горизонтальне масштабування).
