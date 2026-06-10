# Echo Bot — Event-Driven Backend Architecture

> **Ментальна модель:** Telegram Bot — це не "просто бот".  
> Це **event-driven distributed backend system** з async I/O, routing pipeline і observability layer.

```
Update → Dispatcher → Router Chain → Filter Engine → Handler → Observability → Response
```

---

## Diagram 1 — High-Level Telegram Flow

> Повний шлях події від натискання кнопки у Telegram до відповіді бота.

```mermaid
flowchart TB
    subgraph CLIENT["👤 Client Side"]
        U("Telegram App\n(iOS / Android / Web)")
    end

    subgraph INFRA["☁️ Telegram Infrastructure (MTProto + REST)"]
        direction LR
        TS("MTProto Servers\nE2E encrypted transport")
        BOTAPI("Bot API Gateway\napi.telegram.org/bot{token}/...")
    end

    subgraph BOT["🐍 Bot Backend — Python 3.12 + aiogram 3.x"]
        direction TB

        LP["⟳ Long Polling Loop\nGET /getUpdates?offset=N&timeout=30"]

        UPD["Update JSON\n{ update_id, message: { ... } }"]

        subgraph DP["Dispatcher — Central Event Bus"]
            FEED["dp.feed_update(bot, update)\nasync propagation"]
        end

        subgraph CHAIN["Router Chain (ordered)"]
            direction LR
            R1["Router: start\npriority=1"]
            R2["Router: echo\npriority=2  catch-all"]
        end

        subgraph EXEC["Handler Execution"]
            OBS["Observability Layer\nlog_message_metadata()\nlog_full_message()"]
            BL["Business Logic\nformat response"]
            ANS["await message.answer(text)\nasync HTTP → Bot API"]
        end
    end

    subgraph RESPONSE["📤 Telegram API Response"]
        POST["POST /sendMessage\n{ chat_id, text, ... }"]
        ACK["{ ok: true, result: { message_id, ... } }"]
    end

    U -- "user sends message" --> TS
    TS -- "getUpdates (long-poll 30s)" --> BOTAPI
    BOTAPI -- "Update JSON payload" --> LP
    LP -- "parse TelegramObject" --> UPD
    UPD --> FEED
    FEED -- "propagate → first match wins" --> R1
    R1 -- "no match → pass through" --> R2
    R1 & R2 -- "filter matched → execute" --> OBS
    OBS --> BL --> ANS
    ANS -- "HTTPS POST + Bearer token" --> POST
    POST --> TS -- "delivered to user" --> U
    POST --> ACK
```

**Ключові точки:**
- **Long Polling** — бот сам опитує Telegram кожні 30 секунд. Альтернатива: webhook (Telegram пушить до бота).
- **Update JSON** — Telegram надсилає весь об'єкт: `update_id`, `message`, `from_user`, `chat`. aiogram парсить це у Pydantic-моделі.
- **Один HTTP-запит = одна подія** = один прохід через весь pipeline.

---

## Diagram 2 — aiogram Internal Routing Pipeline

> Як aiogram вирішує, який handler викликати. Перший збіг виграє — далі пошук зупиняється.

```mermaid
flowchart TD
    UPD(["Update arrives\nmessage.content_type = ?"])

    subgraph DP["Dispatcher"]
        direction TB

        subgraph R1["Router: start  (registered first — higher priority)"]
            direction TB
            H1["CommandStart()\n→ cmd_start()"]
            H2["Command('help')\n→ cmd_help()"]
            H3["Command('about')\n→ cmd_about()"]
            H4["F.text == 'ℹ️ Про бота'\n→ btn_about()  delegates to cmd_about()"]
            H5["F.text == '❓ Допомога'\n→ btn_help()   delegates to cmd_help()"]
        end

        MISS1{{"no match\nin start router"}}

        subgraph R2["Router: echo  (registered second — lower priority)"]
            direction TB
            H6["F.text\n→ echo_text()"]
            H7["F.photo\n→ echo_photo()"]
            H8["F.sticker\n→ echo_sticker()"]
            H9["@router.message()  ← catch-all\n→ echo_unknown()  WARNING log"]
        end

        STOP(["✅ Handler executed\nstop propagation"])
    end

    UPD --> H1
    H1 -- "not /start" --> H2
    H2 -- "not /help" --> H3
    H3 -- "not /about" --> H4
    H4 -- "not 'ℹ️ Про бота'" --> H5
    H5 -- "no match" --> MISS1
    MISS1 --> H6
    H6 -- "not text" --> H7
    H7 -- "not photo" --> H8
    H8 -- "not sticker" --> H9
    H1 & H2 & H3 & H4 & H5 & H6 & H7 & H8 & H9 --> STOP
```

**Чому порядок роутерів критичний:**

```python
# bot.py — порядок реєстрації = порядок пошуку
dp.include_router(start.router)   # 1. команди + кнопки клавіатури
dp.include_router(echo.router)    # 2. ехо + fallback
```

Якби `echo.router` стояв першим — `F.text` перехопив би натискання кнопок `"ℹ️ Про бота"` до того, як `start.router` міг би їх обробити.

---

## Diagram 3 — Event Loop & Async Concurrency

> Як `asyncio` дозволяє одному процесу обслуговувати сотні користувачів одночасно без threading.

```mermaid
sequenceDiagram
    participant EL as ⚙️ asyncio Event Loop
    participant A  as 👤 User A
    participant B  as 👤 User B
    participant C  as 👤 User C
    participant TG as ☁️ Telegram API

    Note over EL: dp.start_polling() — нескінченний цикл

    A  ->> EL: Update received → echo_text() scheduled
    B  ->> EL: Update received → echo_photo() scheduled
    C  ->> EL: Update received → echo_sticker() scheduled

    Note over EL: Черга задач: [A, B, C]

    EL ->> A:  resume — log_message_metadata()
    A  -->> EL: await message.answer() ← IO suspend

    Note over EL: A чекає IO → переключаємось на B (cooperative multitasking)

    EL ->> B:  resume — log_message_metadata()
    B  -->> EL: await message.answer() ← IO suspend

    Note over EL: B чекає IO → переключаємось на C

    EL ->> C:  resume — log_message_metadata()
    C  -->> EL: await message.answer() ← IO suspend

    Note over EL: Всі 3 чекають IO → Event Loop вільний

    TG -->> EL: HTTP 200 OK (response for A)
    EL ->> A:  resume — sendMessage complete ✓

    TG -->> EL: HTTP 200 OK (response for B)
    EL ->> B:  resume — sendMessage complete ✓

    TG -->> EL: HTTP 200 OK (response for C)
    EL ->> C:  resume — sendMessage complete ✓

    Note over A,C: Всі 3 отримали відповідь ~одночасно<br/>Один процес, нуль threads, нуль blocking
```

**Синхронний vs Асинхронний:**

```
Sync (blocking):
  User A  ████████████ 3s
  User B              ████████████ 3s
  User C                          ████████████ 3s
  Total: 9 seconds

Async (non-blocking):
  User A  ████████████ 3s
  User B  ████████████ 3s   ← паралельно!
  User C  ████████████ 3s   ← паралельно!
  Total: ~3 seconds
```

Ключ — `await`: коли handler чекає відповіді від Telegram API, Event Loop перемикається на іншу задачу.

---

## Diagram 4 — Observability Layer

> Що і де логується в echo_bot. Production-style structured logging.

```mermaid
flowchart LR
    subgraph IN["📥 Incoming Update"]
        MSG("Message\nTelegramObject")
    end

    subgraph OBS["📋 Observability Pipeline (echo.py)"]
        direction TB

        META["log_message_metadata()\n━━━━━━━━━━━━━━━━━━━\nINFO | message_id\nINFO | chat_id / chat_type\nINFO | user_id / username\nINFO | content_type\nINFO | date"]

        FULL["log_full_message()\n━━━━━━━━━━━━━━━━━━━\nDEBUG | message.model_dump(mode='json')\nDEBUG | Full JSON — all fields\nDEBUG | Nested objects: from, chat, photo..."]

        ROUTE["Handler Decision\n━━━━━━━━━━━━━━━━━━━\nINFO  | TEXT MESSAGE RECEIVED | text=...\nINFO  | PHOTO RECEIVED | photo_sizes=N\nINFO  | STICKER RECEIVED | emoji= set=\nWARN  | UNKNOWN CONTENT TYPE | type=..."]

        SEND["Outgoing Log\n━━━━━━━━━━━━━━━━━━━\nINFO  | SENDING RESPONSE | chat_id=\nDEBUG | sent_message.model_dump() — full JSON"]
    end

    subgraph LEVELS["Log Levels"]
        direction TB
        DBG("DEBUG\nFull JSON dumps\nПовна трасировка")
        INF("INFO\nНормальний потік\nМетадані подій")
        WRN("WARNING\nНепередбачений контент\ncatch-all спрацював")
        ERR("ERROR\nAPI помилка\nException в handler")
        CRT("CRITICAL\nBot shutdown\nUnhandled exception")
    end

    subgraph FUTURE["📊 Production Extension"]
        PROM("Prometheus\nmessages_total counter\nlatency histogram")
        GFNA("Grafana\nDashboard\nAlerts")
        SNTR("Sentry\nError tracking\nException context")
        ELK("ELK Stack\nElasticsearch\nKibana search")
    end

    MSG --> META --> FULL --> ROUTE --> SEND
    INF -.->|"log_message_metadata()"| META
    DBG -.->|"log_full_message()"| FULL
    WRN -.->|"echo_unknown()"| ROUTE
    SEND -.->|"sent_message log"| DBG

    SEND --> PROM --> GFNA
    ERR --> SNTR
    INF --> ELK
```

**Налаштування рівня логування:**

```bash
# .env
LOG_LEVEL=DEBUG   # повний JSON кожного update
LOG_LEVEL=INFO    # тільки metadata (production default)
LOG_LEVEL=WARNING # тільки аномалії
```

---

## Diagram 5 — Telegram Update Object Schema

> Структура JSON, який Telegram надсилає боту. aiogram парсить це у Pydantic-моделі.

```mermaid
classDiagram
    class Update {
        +int update_id
        +Message message
        +CallbackQuery callback_query
        +InlineQuery inline_query
        +PollAnswer poll_answer
    }

    class Message {
        +int message_id
        +User from_user
        +Chat chat
        +datetime date
        +str text
        +List~PhotoSize~ photo
        +Sticker sticker
        +Document document
        +Video video
        +ContentType content_type
        +model_dump(mode) dict
    }

    class User {
        +int id
        +bool is_bot
        +str first_name
        +str last_name
        +str username
        +str language_code
    }

    class Chat {
        +int id
        +str type
        +str title
        +str username
    }

    class PhotoSize {
        +str file_id
        +str file_unique_id
        +int width
        +int height
        +int file_size
    }

    class Sticker {
        +str file_id
        +int width
        +int height
        +str emoji
        +str set_name
        +StickerType type
    }

    class ContentType {
        <<enumeration>>
        TEXT
        PHOTO
        STICKER
        DOCUMENT
        VIDEO
        VOICE
        UNKNOWN
    }

    Update "1" --> "0..1" Message : contains
    Message "1" --> "1" User : from_user
    Message "1" --> "1" Chat : chat
    Message "1" --> "0..*" PhotoSize : photo sizes
    Message "1" --> "0..1" Sticker : sticker
    Message --> ContentType : content_type
```

**Як aiogram читає цей JSON:**

```python
# Telegram надсилає raw JSON:
# { "update_id": 123, "message": { "message_id": 456, "from": {...}, "text": "hello" } }

# aiogram автоматично парсить у Pydantic:
message.from_user.id        # int
message.from_user.username  # str | None
message.chat.type           # "private" | "group" | "supergroup" | "channel"
message.content_type        # ContentType.TEXT

# model_dump() — назад у JSON для логування:
message.model_dump(mode="json")  # → dict, JSON serializable
```

---

## Diagram 6 — Production Scaling Path

> Від навчального polling-бота до production-ready горизонтально масштабованої системи.

```mermaid
flowchart TB
    subgraph INTERNET["🌐 Public Internet"]
        TG("☁️ Telegram Servers\nMTProto + Bot API")
        USERS("👥 Users\n1 → 1,000,000+")
    end

    subgraph EDGE["🔒 Edge Layer"]
        NGINX("Nginx\nSSL Termination\nHTTP → HTTPS redirect\nRate Limiting (req/s)")
    end

    subgraph GATEWAY["⚡ API Gateway"]
        FASTAPI("FastAPI\nWebhook endpoint POST /webhook/{secret}\nSecret token validation\nUpdate parsing")
    end

    subgraph WORKERS["🐍 aiogram Workers (horizontal scale)"]
        direction LR
        W1("Worker 1\naiogram Dispatcher")
        W2("Worker 2\naiogram Dispatcher")
        W3("Worker N\naiogram Dispatcher")
    end

    subgraph QUEUE["📨 Message Queue"]
        REDIS_Q("Redis Streams\nor RabbitMQ\nUpdate distribution")
    end

    subgraph STATE["💾 Persistent State"]
        direction LR
        PG("PostgreSQL\nUsers\nSubscriptions\nMessages")
        REDIS_S("Redis\nFSM Storage\nSession Cache\nRate Limiting")
    end

    subgraph OBSERVABILITY["📊 Observability Stack"]
        direction LR
        PROM("Prometheus\nmetrics scraping")
        GRAF("Grafana\nDashboards\nAlerts")
        SENTRY("Sentry\nError tracking\nStack traces")
        LOKI("Loki + Grafana\nLog aggregation")
    end

    subgraph CICD["🚀 CI/CD"]
        GH("GitHub Actions\ntest → build → deploy")
        REG("Container Registry\nDocker image")
    end

    USERS -- "send messages" --> TG
    TG -- "POST /webhook/{secret}\nHTTPS push" --> NGINX
    NGINX -- "proxy_pass" --> FASTAPI
    FASTAPI -- "validate secret token\npublish update" --> REDIS_Q
    REDIS_Q -- "consume updates" --> W1 & W2 & W3
    W1 & W2 & W3 -- "read/write state" --> PG & REDIS_S
    W1 & W2 & W3 -- "POST /sendMessage" --> TG
    W1 & W2 & W3 -- "metrics + logs" --> PROM & SENTRY & LOKI
    PROM --> GRAF
    LOKI --> GRAF
    GH --> REG --> W1
```

**Еволюція архітектури:**

| Стадія | Підхід | Юзери | Складність |
|--------|--------|-------|------------|
| ⭐ Echo Bot (зараз) | Long Polling, 1 процес | 1–100 | Мінімальна |
| ⭐⭐ AI Bot | Long Polling + Redis | 100–1K | Середня |
| ⭐⭐⭐ Production | Webhook + FastAPI + PostgreSQL | 1K–100K | Висока |
| 🚀 Scale | Webhook + Workers + Redis Streams | 100K+ | Розподілена |

**Перехід Polling → Webhook:**

```python
# Polling (розробка):
await dp.start_polling(bot, drop_pending_updates=True)
# Бот сам питає Telegram кожні 30 сек

# Webhook (production):
await bot.set_webhook(url="https://yourdomain.com/webhook/SECRET")
# Telegram сам пушить updates до бота — менше затримка, менше трафік
```

---

## Backend Engineering Mental Model

```
Telegram Bot
  = Event-Driven System
    + Async I/O Runtime
    + Routing Pipeline
    + Observability Layer

Event
  = Update (JSON from Telegram)

Event-Driven
  = handler виконується тільки при надходженні події
  = система не "поллює" постійно — вона реагує

Async I/O
  = один потік обслуговує N одночасних з'єднань
  = await = "паузую цю задачу, роби інших, повернись коли IO готово"

Routing Pipeline
  = Update → Dispatcher → Router → Filter → Handler
  = кожен рівень звужує набір можливих handlers

Observability
  = логи (що сталось) + метрики (скільки/як довго) + трейси (де)
  = без observability — система "чорна скринька"
```
