# FastAPI — Документація: Архітектура, Async та Production Patterns

**Модуль:** 4 — Network & Concurrent Systems  
**Складність:** intermediate → advanced  
**Мова:** Українська

---

## Зміст

1. [Що таке FastAPI?](#1-що-таке-fastapi)
2. [ASGI vs WSGI](#2-asgi-vs-wsgi)
3. [Три типи ендпоінтів та їх поведінка](#3-три-типи-ендпоінтів-та-їх-поведінка)
4. [Blocking Code: Каскадний Ефект](#4-blocking-code-каскадний-ефект)
5. [Dependency Injection (DI)](#5-dependency-injection-di)
6. [Async Connection Pool з asyncpg](#6-async-connection-pool-з-asyncpg)
7. [Repository Pattern](#7-repository-pattern)
8. [Unit of Work Pattern](#8-unit-of-work-pattern)
9. [Мікросервісна Архітектура](#9-мікросервісна-архітектура)
10. [Production Deployment](#10-production-deployment)
11. [Mermaid Діаграми](#11-mermaid-діаграми)

---

## 1. Що таке FastAPI?

FastAPI — сучасний Python вебфреймворк для побудови REST API, порівнянний за швидкістю з Node.js та Go. Побудований на двох стовпах:

| Компонент | Роль |
|-----------|------|
| **Starlette** | ASGI toolkit — async HTTP, WebSocket, middleware |
| **Pydantic** | Валідація типів, серіалізація JSON, автодокументація |

### Ключові можливості

**Автоматична документація** — FastAPI генерує Swagger UI та ReDoc з коду:
```
http://localhost:8000/docs    ← Swagger UI (інтерактивний)
http://localhost:8000/redoc   ← ReDoc (читабельний)
http://localhost:8000/openapi.json ← OpenAPI schema
```

**Type hints → Валідація** — Pydantic перехоплює неправильні дані до входу в бізнес-логіку:
```python
@app.get("/users/{user_id}")
async def get_user(user_id: int, limit: int = 10):
    # FastAPI автоматично:
    # 1. Парсить user_id з URL як int (400 якщо не число)
    # 2. Читає limit з query string (default=10)
    # 3. Валідує через Pydantic
    ...
```

**Dependency Injection** — система ін'єкцій залежностей вбудована у фреймворк (детальніше у розділі 5).

---

## 2. ASGI vs WSGI

```
WSGI (синхронний):                 ASGI (асинхронний):
┌──────────────┐                   ┌──────────────┐
│  Nginx/Proxy │                   │  Nginx/Proxy │
└──────┬───────┘                   └──────┬───────┘
       │                                  │
┌──────▼────────────────┐         ┌──────▼────────────────┐
│  Gunicorn             │         │  uvicorn              │
│  4 worker processes   │         │  1 async process      │
│  (4 × Python interp.) │         │  Event Loop           │
└──────┬───────┬────────┘         └──────┬────────────────┘
       │       │                         │
   [Thread] [Thread]               [Coroutine × 10000]
   per request                     all in one thread
```

### Чому ASGI виграє для I/O-bound навантажень

| | WSGI (Gunicorn) | ASGI (uvicorn) |
|--|-----------------|----------------|
| Модель | 1 process / request | 1 coroutine / request |
| Пам'ять/з'єднання | ~8 MB (thread) | ~2 KB (coroutine) |
| Max concurrent | ~100–500 | ~10 000+ |
| WebSocket | Складно | Нативно |
| CPU-bound | ОК (процеси) | Потрібен executor |

---

## 3. Три типи ендпоінтів та їх поведінка

Це критично важливо зрозуміти перед написанням будь-якого FastAPI коду:

```python
from fastapi import FastAPI
import asyncio, time

app = FastAPI()

# ────────────────────────────────────────────────────────────────
# ТИП 1: async def + await  →  Event Loop (НАЙКРАЩЕ для I/O)
# ────────────────────────────────────────────────────────────────
@app.get("/type1")
async def type1():
    await asyncio.sleep(2)     # ✅ Event Loop вільний
    return {"type": 1}

# ────────────────────────────────────────────────────────────────
# ТИП 2: async def + blocking  →  КАТАСТРОФА
# ────────────────────────────────────────────────────────────────
@app.get("/type2")
async def type2():
    time.sleep(2)              # ⛔ Замораживає весь сервер!
    return {"type": 2}

# ────────────────────────────────────────────────────────────────
# ТИП 3: def (sync)  →  Автоматичний ThreadPool (безпечно, обмежено)
# ────────────────────────────────────────────────────────────────
@app.get("/type3")
def type3():
    time.sleep(2)              # ⚠️  OK — FastAPI детектує def → threadpool
    return {"type": 3}
```

### Шкала виконання для 1000 клієнтів

```
ТИП 1 (async + await):
  [T=0ms]    1000 coroutines стартують
  [T=0.5ms]  Всі 1000 await asyncio.sleep() — Event Loop ВІЛЬНИЙ
  [T=2000ms] Всі 1000 прокидаються одночасно
  Throughput: ~500 req/s  ✅

ТИП 2 (async + blocking):
  [T=0ms]    Запит #1 → time.sleep(2) → Event Loop ЗАМЕРЗ
  [T=2000ms] Запит #1 відповів → Запит #2 стартує
  [T=4000ms] Запит #2 відповів → Запит #3...
  Throughput: 0.5 req/s  ❌  (1000× гірше!)

ТИП 3 (sync def → threadpool):
  FastAPI: виявлено def → spawn thread
  40 threads обслуговують 40 запитів паралельно
  960 запитів чекають у черзі
  Throughput: ~20 req/s  ⚠️
```

---

## 4. Blocking Code: Каскадний Ефект

### Чому один blocking виклик руйнує весь сервер

Уяви ресторан з одним офіціантом (Event Loop). Якщо офіціант йде на кухню і сам готує страву (blocking call) — всі інші клієнти чекають. Ніхто не приймає нових замовлень, ніхто не отримує рахунки.

```
Клієнт A:  ──────[ЗАМОВЛЕННЯ]──────[time.sleep 2s — весь сервер чекає]──[ВІДПОВІДЬ]
Клієнт B:  ─────────────────────────────────────────────[Тепер може стартувати]──[відповідь]
Клієнт C:  ──────────────────────────────────────────────────────────────────────[стартує]
```

### Таблиця замін

| Blocking (ЗАБОРОНЕНО в async def) | Non-blocking (ПРАВИЛЬНО) |
|------------------------------------|--------------------------|
| `time.sleep(n)` | `await asyncio.sleep(n)` |
| `requests.get(url)` | `await session.get(url)` (aiohttp / httpx async) |
| `open(path).read()` | `await aio_file.read()` (aiofiles) |
| `psycopg2.execute(sql)` | `await conn.fetch(sql)` (asyncpg) |
| `subprocess.run(cmd)` | `await asyncio.create_subprocess_exec(...)` |
| CPU-bound loop | `await loop.run_in_executor(process_pool, func)` |

---

## 5. Dependency Injection (DI)

FastAPI має вбудовану DI-систему через `Depends()`. Це один з найпотужніших інструментів фреймворку.

### Базовий приклад

```python
from fastapi import FastAPI, Depends, Header, HTTPException

app = FastAPI()

# Залежність: перевірка API ключа
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "secret-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Залежність: pagination параметри
def get_pagination(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": min(limit, 1000)}

# Ендпоінт використовує обидві залежності
@app.get("/items")
async def list_items(
    api_key: str = Depends(verify_api_key),
    pagination: dict = Depends(get_pagination),
):
    return {"items": [], **pagination}
```

### DI Lifecycle: від Request до Response

```
HTTP Request
    │
    ▼
FastAPI Router розбирає маршрут
    │
    ▼
DI System викликає всі Depends() ─────────────────────────────┐
    │                                                          │
    ├── verify_api_key(header) ──────────────── перевірка     │
    ├── get_pagination(query)  ──────────────── параметри     │
    └── get_db_connection()    ──────────────── з'єднання з БД│
            │ (yield conn)                                     │
            ▼                                                  │
    Ендпоінт-функція отримує готові залежності                │
            │                                                  │
            ▼                                                  │
    Генерує відповідь                                         │
            │                                                  │
    DI System завершує залежності (після yield) ◄─────────────┘
            │ (закриття з'єднань, cleanup)
            ▼
HTTP Response
```

### yield-залежності — гарантований cleanup

```python
async def get_db_connection(pool):
    async with pool.acquire() as conn:
        yield conn          # ← передаємо в ендпоінт
    # Тут автоматично: conn.release() назад у pool
    # НАВІТЬ якщо ендпоінт кинув виняток!
```

---

## 6. Async Connection Pool з asyncpg

### Чому connection pool критично важливий

Відкриття нового TCP-з'єднання з PostgreSQL — дорога операція (~50ms, TCP handshake + auth). Якщо 1000 клієнтів відкривають нові з'єднання одночасно — БД відмовляє через `max_connections` (~100 за замовчуванням).

**Connection pool** тримає N вже відкритих з'єднань. Клієнти беруть з'єднання з пулу (~0.1ms) і повертають після запиту.

### Реалізація з asyncpg

```python
import asyncpg
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

db_pool: asyncpg.Pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    # ─── Startup ───────────────────────────────────────────────
    db_pool = await asyncpg.create_pool(
        dsn="postgresql://user:pass@localhost/mydb",
        min_size=5,    # Мінімум відкритих з'єднань (warm)
        max_size=20,   # Максимум одночасних з'єднань
        command_timeout=30,  # Timeout для SQL запиту
    )
    yield
    # ─── Shutdown ──────────────────────────────────────────────
    await db_pool.close()  # Закрити всі з'єднання

app = FastAPI(lifespan=lifespan)

# DI: отримати з'єднання з пулу на час запиту
async def get_db():
    async with db_pool.acquire() as conn:
        yield conn  # FastAPI гарантує release після запиту

@app.get("/users/{user_id}")
async def get_user(user_id: int, conn = Depends(get_db)):
    row = await conn.fetchrow(
        "SELECT id, name, email FROM users WHERE id = $1",
        user_id
    )
    if not row:
        raise HTTPException(status_code=404)
    return dict(row)
```

### Execution Timeline для двох одночасних запитів

```
[T=0ms]    Клієнт A: db_pool.acquire() → з'єднання #1 (миттєво з пулу)
[T=0ms]    Клієнт B: db_pool.acquire() → з'єднання #2 (миттєво з пулу)

[T=1ms]    A: SQL → байти → мережевий сокет до PostgreSQL
[T=1ms]    B: SQL → байти → мережевий сокет до PostgreSQL

[T=2ms]    A: await conn.fetch() → SUSPENDED (Event Loop вільний!)
[T=2ms]    B: await conn.fetch() → SUSPENDED (Event Loop вільний!)

[T=52ms]   PostgreSQL відповів B → Event Loop прокидає B
[T=60ms]   PostgreSQL відповів A → Event Loop прокидає A

[T=61ms]   A завершено → з'єднання #1 повернуто в пул
[T=61ms]   B завершено → з'єднання #2 повернуто в пул
```

---

## 7. Repository Pattern

### Проблема: "Сирий SQL" в ендпоінтах

```python
# ❌ Порушення SRP — ендпоінт знає про SQL, asyncpg, схему БД
@app.get("/users/{user_id}")
async def get_user(user_id: int, conn = Depends(get_db)):
    row = await conn.fetchrow(
        "SELECT id, name, email FROM users WHERE id = $1", user_id
    )
    return dict(row) if row else None
```

**Проблеми цього підходу:**
- Тестування вимагає реальної бази даних
- Зміна БД вимагає зміни ендпоінтів
- SQL розсипаний по всьому коду

### Рішення: Repository абстракція

```python
import abc
from typing import Optional
from pydantic import BaseModel

# ─── Доменна модель (бізнес-об'єкт) ──────────────────────────────────────────
class User(BaseModel):
    id: int
    name: str
    email: str

# ─── Абстрактний порт (інтерфейс) ─────────────────────────────────────────────
class AbstractUserRepository(abc.ABC):
    @abc.abstractmethod
    async def get(self, user_id: int) -> Optional[User]:
        ...

    @abc.abstractmethod
    async def add(self, user: User) -> None:
        ...

# ─── Конкретний адаптер (asyncpg) ─────────────────────────────────────────────
class AsyncpgUserRepository(AbstractUserRepository):
    def __init__(self, conn):
        self._conn = conn

    async def get(self, user_id: int) -> Optional[User]:
        row = await self._conn.fetchrow(
            "SELECT id, name, email FROM users WHERE id = $1", user_id
        )
        return User(**dict(row)) if row else None

    async def add(self, user: User) -> None:
        await self._conn.execute(
            "INSERT INTO users (id, name, email) VALUES ($1, $2, $3)",
            user.id, user.name, user.email
        )

# ─── Fake репозиторій для тестів ──────────────────────────────────────────────
class InMemoryUserRepository(AbstractUserRepository):
    def __init__(self):
        self._store: dict[int, User] = {}

    async def get(self, user_id: int) -> Optional[User]:
        return self._store.get(user_id)

    async def add(self, user: User) -> None:
        self._store[user.id] = user

# ─── DI: вибір реалізації ─────────────────────────────────────────────────────
async def get_user_repo(conn = Depends(get_db)) -> AbstractUserRepository:
    return AsyncpgUserRepository(conn)

# ─── Ендпоінт — не знає про SQL і asyncpg ─────────────────────────────────────
@app.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    repo: AbstractUserRepository = Depends(get_user_repo)
):
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Переваги Repository Pattern

| Перевага | Деталь |
|----------|--------|
| **Тестованість** | `InMemoryUserRepository` — тести за мілісекунди без БД |
| **Розділення відповідальності** | Ендпоінт ≠ SQL, ендпоінт ≠ ORM |
| **Заміна БД** | Новий `MongoUserRepository` → нуль змін в ендпоінтах |
| **Читабельність** | `repo.get(user_id)` читається як бізнес-логіка |

---

## 8. Unit of Work Pattern

### Проблема: Незавершені транзакції

Якщо твій ендпоінт виконує два SQL запити і падає між ними — дані стають несумісними:

```python
# ❌ Небезпечно: якщо insert_order кине виняток — баланс вже знятий!
await conn.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
await conn.execute("INSERT INTO orders VALUES (...)")  # Може впасти!
```

**Unit of Work** (UoW) гарантує атомарність: або обидві операції успішні (`commit`), або обидві відкочені (`rollback`).

### Реалізація

```python
import abc

# ─── Абстракція UoW ───────────────────────────────────────────────────────────
class AbstractUnitOfWork(abc.ABC):
    users: AbstractUserRepository  # Доступ до репозиторіїв

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, tb):
        await self.rollback()  # Безпечно за замовчуванням!

    @abc.abstractmethod
    async def commit(self): ...

    @abc.abstractmethod
    async def rollback(self): ...

# ─── Конкретна реалізація для asyncpg ────────────────────────────────────────
class AsyncpgUnitOfWork(AbstractUnitOfWork):
    def __init__(self, pool):
        self._pool = pool

    async def __aenter__(self):
        self._conn = await self._pool.acquire()
        self._tx = self._conn.transaction()
        await self._tx.start()
        self.users = AsyncpgUserRepository(self._conn)
        return self

    async def __aexit__(self, exc_type, exc_val, tb):
        await super().__aexit__(exc_type, exc_val, tb)
        await self._pool.release(self._conn)

    async def commit(self):
        await self._tx.commit()

    async def rollback(self):
        await self._tx.rollback()

# ─── Fake UoW для тестів ───────────────────────────────────────────────────────
class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.users = InMemoryUserRepository()
        self.committed = False

    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def commit(self): self.committed = True
    async def rollback(self): pass

# ─── Сервісний шар (бізнес-логіка) ───────────────────────────────────────────
async def transfer_funds(
    from_id: int, to_id: int, amount: float,
    uow: AbstractUnitOfWork
) -> None:
    async with uow:
        sender = await uow.users.get(from_id)
        receiver = await uow.users.get(to_id)

        if sender.balance < amount:
            raise ValueError("Insufficient funds")

        sender.balance -= amount
        receiver.balance += amount

        await uow.users.update(sender)
        await uow.users.update(receiver)

        await uow.commit()  # Атомарно: обидва UPDATE або нічого

# ─── FastAPI ендпоінт ─────────────────────────────────────────────────────────
async def get_uow():
    yield AsyncpgUnitOfWork(db_pool)

@app.post("/transfer")
async def transfer_endpoint(
    from_id: int, to_id: int, amount: float,
    uow: AbstractUnitOfWork = Depends(get_uow)
):
    # Ендпоінт не містить ні SQL, ні транзакцій, ні БД деталей!
    await transfer_funds(from_id, to_id, amount, uow)
    return {"status": "transferred"}
```

### UoW Execution Timeline

```
[T=0]  HTTP POST /transfer
[T=1]  DI: get_uow() → AsyncpgUnitOfWork(pool)
[T=2]  async with uow: → __aenter__
       ├── pool.acquire() → з'єднання #5
       └── transaction.start() → BEGIN TRANSACTION (SQL)
[T=3]  transfer_funds() виконується
[T=4]  commit() → COMMIT TRANSACTION (SQL)
[T=5]  __aexit__: rollback() ігнорується (вже committed)
[T=6]  pool.release(conn) → з'єднання #5 повернуто
[T=7]  HTTP 200 Response

--- Якщо виникає виняток між T=3 і T=4: ---
[T=E]  Exception кинуто
[T=E+1] __aexit__(exc_type=...) → rollback() → ROLLBACK (SQL)
[T=E+2] pool.release(conn)
[T=E+3] HTTP 500 Response (дані не змінені!)
```

### Тестування з FakeUoW

```python
import pytest

@pytest.mark.asyncio
async def test_transfer_funds():
    uow = FakeUnitOfWork()
    uow.users._store = {
        1: User(id=1, balance=500),
        2: User(id=2, balance=100),
    }

    await transfer_funds(1, 2, 200, uow)

    assert uow.committed is True
    assert uow.users._store[1].balance == 300
    assert uow.users._store[2].balance == 300
    # Тест за мілісекунди, без реальної БД!
```

---

## 9. Мікросервісна Архітектура

### FastAPI у мікросервісній системі

```
                         Клієнти
                  ┌────────┴────────┐
               Browser           Mobile App
                  └────────┬────────┘
                           │
                    ┌──────▼──────┐
                    │ API Gateway  │  (nginx / Traefik)
                    │ Load Balancer│
                    └──┬───┬───┬──┘
                       │   │   │
              ┌────────┘   │   └────────┐
              │            │            │
        ┌─────▼──────┐ ┌───▼────┐ ┌────▼──────┐
        │  FastAPI   │ │FastAPI │ │  FastAPI  │
        │  Users     │ │Orders  │ │  Payments │
        │  Service   │ │Service │ │  Service  │
        └─────┬──────┘ └───┬────┘ └────┬──────┘
              │             │           │
        ┌─────▼──────┐ ┌───▼────┐ ┌────▼──────┐
        │PostgreSQL  │ │MongoDB │ │  Redis    │
        └────────────┘ └────────┘ └───────────┘
```

### BFF (Backend for Frontend)

```python
# Агрегатор для мобільного клієнта — збирає дані з кількох сервісів
@app.get("/mobile/dashboard/{user_id}")
async def mobile_dashboard(user_id: int):
    async with aiohttp.ClientSession() as session:
        # Паралельно запитуємо 3 мікросервіси
        user_data, orders, balance = await asyncio.gather(
            fetch_user(session, user_id),
            fetch_orders(session, user_id),
            fetch_balance(session, user_id),
        )
    return {"user": user_data, "orders": orders, "balance": balance}
```

---

## 10. Production Deployment

### Стек розгортання

```
Internet
    │
[ Traefik / Nginx ]     ← TLS termination, load balancing, static files
    │
[ uvicorn ]             ← ASGI server, 1+ workers
    │
[ FastAPI app ]         ← application code
    │
[ asyncpg pool ]        ← 5–20 persistent connections
    │
[ PostgreSQL ]          ← database
```

### docker-compose.yml (production-ready)

```yaml
services:
  api:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    environment:
      - DATABASE_URL=postgresql://user:pass@db/mydb
    depends_on:
      db:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 512M

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Кількість uvicorn workers

```
# Правило: (2 × CPU cores) + 1
# Для I/O-bound FastAPI — часто достатньо 1–2 worker
# ProcessPoolExecutor у worker обробляє CPU-bound задачі

uvicorn main:app --workers 4    # 4 незалежних Event Loop
```

---

## 11. Mermaid Діаграми

### Діаграма 1: FastAPI Request Lifecycle

```mermaid
flowchart TD
    REQ([HTTP Request]) --> UVICORN[uvicorn\nASGI Server]
    UVICORN --> MIDDLEWARE[Middleware Stack\nCORS / Auth / Logging]
    MIDDLEWARE --> ROUTER[FastAPI Router\nмаршрутизація за URL]
    ROUTER --> DETECT{Тип\nфункції?}

    DETECT -- "async def" --> DI_ASYNC[DI System\nвиконує Depends async]
    DETECT -- "def sync" --> THREADPOOL[ThreadPoolExecutor\nокремий потік]

    DI_ASYNC --> DEPS_CHECK{Blocking\nу залежностях?}
    DEPS_CHECK -- "await (OK)" --> HANDLER_ASYNC[Async Handler\nEvent Loop вільний]
    DEPS_CHECK -- "blocking (❌)" --> FREEZE[⛔ Event Loop\nЗАМОРОЖЕНИЙ]

    HANDLER_ASYNC --> PYDANTIC[Pydantic\nСеріалізація відповіді]
    THREADPOOL --> PYDANTIC
    PYDANTIC --> RESP([HTTP Response JSON])

    FREEZE --> BLOCK_ALL[Всі клієнти чекають!]
```

---

### Діаграма 2: Connection Pool Lifecycle

```mermaid
sequenceDiagram
    participant A as Клієнт A
    participant B as Клієнт B
    participant C as Клієнт C
    participant P as Connection Pool (max=2)
    participant DB as PostgreSQL

    A->>P: pool.acquire()
    P-->>A: з'єднання #1 (миттєво!)
    B->>P: pool.acquire()
    P-->>B: з'єднання #2 (миттєво!)

    C->>P: pool.acquire()
    P-->>C: ⏳ Semaphore.acquire() — SUSPEND

    A->>DB: await conn.fetchrow(SQL)
    B->>DB: await conn.fetchrow(SQL)
    Note over A,B: Обидва чекають відповідь БД<br/>Event Loop вільний!

    DB-->>A: Result A
    A->>P: conn.release() → з'єднання #1 повернуто
    P-->>C: з'єднання #1 передано клієнту C!
    C->>DB: await conn.fetchrow(SQL)

    DB-->>B: Result B
    B->>P: conn.release()
    DB-->>C: Result C
    C->>P: conn.release()
```

---

### Діаграма 3: Repository + DI Pattern

```mermaid
flowchart LR
    subgraph HTTP["HTTP Layer (FastAPI)"]
        EP["@app.get\n/users/{id}"]
    end

    subgraph DI["Dependency Injection"]
        DEPS["Depends(get_user_repo)"]
    end

    subgraph REPO["Repository Layer"]
        ABS["AbstractUserRepository\n(abc.ABC)"]
        ASYNCPG["AsyncpgUserRepository\n(production)"]
        FAKE["InMemoryUserRepository\n(tests)"]
    end

    subgraph INFRA["Infrastructure"]
        PG[(PostgreSQL\nasyncpg)]
        MEM[("dict in memory\n(tests)")]
    end

    EP -->|"user_id: int\nrepo: AbstractUserRepository"| DEPS
    DEPS -->|"prod"| ASYNCPG
    DEPS -->|"test"| FAKE
    ASYNCPG --> ABS
    FAKE --> ABS
    ASYNCPG --> PG
    FAKE --> MEM
    ABS -->|"await repo.get(user_id)"| EP
```

---

### Діаграма 4: Unit of Work — Transaction Safety

```mermaid
stateDiagram-v2
    direction LR

    [*] --> IDLE : FastAPI отримує запит

    IDLE --> CONNECTING : async with uow:\n__aenter__()
    CONNECTING --> ACTIVE : pool.acquire()\ntransaction.start()\nBEGIN SQL

    ACTIVE --> WORKING : Бізнес-логіка\nrepo.add() / update()

    WORKING --> COMMITTED : await uow.commit()\nCOMMIT SQL ✅
    WORKING --> ROLLEDBACK : Exception!\n__aexit__(exc)\nROLLBACK SQL ⛔

    COMMITTED --> RELEASE : pool.release(conn)
    ROLLEDBACK --> RELEASE : pool.release(conn)

    RELEASE --> [*] : HTTP Response

    note right of ROLLEDBACK
        Безпека за замовчуванням:
        __aexit__ ЗАВЖДИ викликає rollback()
        якщо commit() не був явним
    end note
```

---

### Діаграма 5: Microservices Architecture

```mermaid
flowchart TD
    Browser([Browser SPA]) --> GW
    Mobile([Mobile App]) --> BFF

    GW[API Gateway\nTraefik / Nginx\nTLS + Rate Limiting]
    BFF[BFF Service\nFastAPI\nАгрегатор для Mobile]

    GW --> US[Users Service\nFastAPI + asyncpg]
    GW --> OS[Orders Service\nFastAPI + MongoDB]
    GW --> PS[Payments Service\nFastAPI + Redis]

    BFF --> US
    BFF --> OS
    BFF --> PS

    US --> PG[(PostgreSQL)]
    OS --> MONGO[(MongoDB)]
    PS --> REDIS[(Redis)]

    US -.->|"async events"| MQ[[Message Queue\nRabbitMQ / Kafka]]
    OS -.->|"async events"| MQ
    PS -.->|"async events"| MQ
    MQ -.-> NOTIFY[Notification Service\nEmail / Push]
```

---

### Діаграма 6: WSGI vs ASGI під навантаженням

```mermaid
xychart-beta
    title "Throughput під навантаженням (req/s)"
    x-axis [10, 50, 100, 500, 1000, 5000]
    y-axis "req/s" 0 --> 2000
    line "ASGI FastAPI (async)" [95, 490, 980, 1800, 1950, 1990]
    line "WSGI Gunicorn (4 workers)" [95, 380, 600, 650, 640, 620]
    line "async def + blocking" [5, 5, 5, 5, 5, 5]
```

---

## Швидкий чеклист перед деплоєм FastAPI

```
□ Всі DB/HTTP виклики використовують await (asyncpg, aiohttp, httpx)
□ Жодного time.sleep() в async def
□ Connection pool ініціалізується в lifespan (не per-request)
□ DI через yield гарантує release з'єднань
□ CPU-bound задачі делеговані в ProcessPoolExecutor
□ Repository Pattern відокремлює SQL від бізнес-логіки
□ UoW Pattern гарантує атомарність транзакцій
□ Fake репозиторії покривають юніт-тести
□ uvicorn --workers = (2 × cpu_count) + 1
□ Pydantic response_model валідує вихідні дані
```
